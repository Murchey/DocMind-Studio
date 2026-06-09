"""
Schedule Solver - 排课约束求解器
使用回溯算法和启发式策略生成排课方案
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class Assignment:
    """排课分配"""
    course_id: str
    course_name: str
    teacher_id: str
    teacher_name: str
    class_id: str
    class_name: str
    room_id: str
    room_name: str
    time_slot_id: str
    day: str
    period: int
    time: str


@dataclass
class CourseSlot:
    """课程待分配槽位"""
    course_id: str
    course_name: str
    teacher_id: str
    teacher_name: str
    class_id: str
    class_name: str
    consecutive: int = 1
    required_hours: int = 1


class ScheduleSolver:
    """排课约束求解器"""
    
    def __init__(self):
        self.teachers: Dict[str, Dict] = {}
        self.courses: List[Dict] = []
        self.classrooms: Dict[str, Dict] = {}
        self.classes: Dict[str, Dict] = {}
        self.time_slots: Dict[str, Dict] = {}
        self.constraints: Dict[str, List] = {"hard": [], "soft": []}
        
        # 冲突检测集合
        self.teacher_time_used: Dict[str, Set[str]] = {}  # teacher_id -> set of time_slot_id
        self.class_time_used: Dict[str, Set[str]] = {}    # class_id -> set of time_slot_id
        self.room_time_used: Dict[str, Set[str]] = {}     # room_id -> set of time_slot_id
        
        # 结果
        self.assignments: List[Assignment] = []
        self.unassigned: List[Dict] = []
        self.warnings: List[str] = []
    
    def solve(self, constraints_path: str) -> Dict[str, Any]:
        """
        从 JSON 文件加载约束并求解
        
        Args:
            constraints_path: 约束 JSON 文件路径
            
        Returns:
            排课结果
        """
        with open(constraints_path, 'r', encoding='utf-8') as f:
            constraints = json.load(f)
        
        return self.solve_from_dict(constraints)
    
    def solve_from_dict(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        从字典对象求解
        
        Args:
            constraints: 约束数据字典
            
        Returns:
            排课结果
        """
        # 初始化数据
        self._init_data(constraints)
        
        # 生成待分配槽位
        course_slots = self._generate_course_slots()
        
        # 按 MRV 启发式排序
        course_slots = self._sort_by_mrv(course_slots)
        
        # 回溯求解
        success = self._backtrack(course_slots, 0)
        
        # 生成结果
        return self._generate_result(constraints.get("source_file", ""), success)
    
    def _init_data(self, constraints: Dict[str, Any]):
        """初始化数据结构"""
        # 教师
        for teacher in constraints.get("teachers", []):
            self.teachers[teacher["id"]] = teacher
            self.teacher_time_used[teacher["id"]] = set()
        
        # 课程
        self.courses = constraints.get("courses", [])
        
        # 教室
        for room in constraints.get("classrooms", []):
            self.classrooms[room["id"]] = room
            self.room_time_used[room["id"]] = set()
        
        # 班级
        for cls in constraints.get("classes", []):
            self.classes[cls["id"]] = cls
            self.class_time_used[cls["id"]] = set()
        
        # 时间槽
        for slot in constraints.get("time_slots", []):
            self.time_slots[slot["id"]] = slot
        
        # 约束
        self.constraints = constraints.get("constraints", {"hard": [], "soft": []})
        
        # 建立名称到ID的映射
        self._teacher_name_map = {t.get("name", ""): t["id"] for t in constraints.get("teachers", [])}
        self._class_name_map = {c.get("name", ""): c["id"] for c in constraints.get("classes", [])}
    
    def _generate_course_slots(self) -> List[CourseSlot]:
        """生成待分配的课程槽位"""
        slots = []
        
        for course in self.courses:
            teacher_id = self._teacher_name_map.get(course.get("teacher_name", ""), course.get("teacher_id", ""))
            class_id = self._class_name_map.get(course.get("class_name", ""), course.get("class_id", ""))
            
            # 获取教师和班级信息
            teacher = self.teachers.get(teacher_id, {})
            class_info = self.classes.get(class_id, {})
            
            hours = course.get("hours_per_week", 2)
            consecutive = course.get("consecutive", 1)
            
            # 如果需要连排，将课时分组
            if consecutive > 1:
                num_groups = hours // consecutive
                remaining = hours % consecutive
                
                for i in range(num_groups):
                    slot = CourseSlot(
                        course_id=course["id"],
                        course_name=course["name"],
                        teacher_id=teacher_id,
                        teacher_name=teacher.get("name", course.get("teacher_name", "")),
                        class_id=class_id,
                        class_name=class_info.get("name", course.get("class_name", "")),
                        consecutive=consecutive,
                        required_hours=consecutive
                    )
                    slots.append(slot)
                
                if remaining > 0:
                    slot = CourseSlot(
                        course_id=course["id"],
                        course_name=course["name"],
                        teacher_id=teacher_id,
                        teacher_name=teacher.get("name", course.get("teacher_name", "")),
                        class_id=class_id,
                        class_name=class_info.get("name", course.get("class_name", "")),
                        consecutive=1,
                        required_hours=remaining
                    )
                    slots.append(slot)
            else:
                for i in range(hours):
                    slot = CourseSlot(
                        course_id=course["id"],
                        course_name=course["name"],
                        teacher_id=teacher_id,
                        teacher_name=teacher.get("name", course.get("teacher_name", "")),
                        class_id=class_id,
                        class_name=class_info.get("name", course.get("class_name", "")),
                        consecutive=1,
                        required_hours=1
                    )
                    slots.append(slot)
        
        return slots
    
    def _sort_by_mrv(self, slots: List[CourseSlot]) -> List[CourseSlot]:
        """按最小剩余值（MRV）启发式排序"""
        def count_available_slots(slot: CourseSlot) -> int:
            count = 0
            for slot_id, slot_info in self.time_slots.items():
                if self._is_slot_available(slot, slot_id):
                    count += 1
            return count
        
        # 按可用槽数量升序排序（MRV）
        slots.sort(key=count_available_slots)
        return slots
    
    def _is_slot_available(self, course_slot: CourseSlot, time_slot_id: str) -> bool:
        """检查时间槽是否可用于该课程"""
        # 检查教师可用性
        teacher = self.teachers.get(course_slot.teacher_id, {})
        teacher_available = teacher.get("available_slots", ["all"])
        if "all" not in teacher_available and time_slot_id not in teacher_available:
            return False
        
        # 检查教师冲突
        if time_slot_id in self.teacher_time_used.get(course_slot.teacher_id, set()):
            return False
        
        # 检查班级冲突
        if time_slot_id in self.class_time_used.get(course_slot.class_id, set()):
            return False
        
        return True
    
    def _get_available_rooms(self, course_slot: CourseSlot, time_slot_id: str) -> List[str]:
        """获取可用教室列表"""
        available = []
        class_info = self.classes.get(course_slot.class_id, {})
        class_size = class_info.get("size", 0)
        
        for room_id, room in self.classrooms.items():
            # 检查教室是否已被占用
            if time_slot_id in self.room_time_used.get(room_id, set()):
                continue
            
            # 检查教室容量
            if room.get("capacity", 0) < class_size:
                continue
            
            # 检查教室可用时间
            room_available = room.get("available_slots", ["all"])
            if "all" not in room_available and time_slot_id not in room_available:
                continue
            
            available.append(room_id)
        
        return available
    
    def _backtrack(self, slots: List[CourseSlot], index: int) -> bool:
        """
        回溯求解
        
        Args:
            slots: 待分配槽位列表
            index: 当前处理的槽位索引
            
        Returns:
            是否成功分配所有槽位
        """
        # 所有槽位已分配
        if index >= len(slots):
            return True
        
        current_slot = slots[index]
        
        # 获取可用时间槽
        available_time_slots = []
        for slot_id in self.time_slots:
            if self._is_slot_available(current_slot, slot_id):
                available_time_slots.append(slot_id)
        
        # 按软约束评分排序
        available_time_slots = self._sort_by_soft_constraints(current_slot, available_time_slots)
        
        for time_slot_id in available_time_slots:
            # 获取可用教室
            available_rooms = self._get_available_rooms(current_slot, time_slot_id)
            
            if not available_rooms:
                continue
            
            # 选择第一个可用教室
            room_id = available_rooms[0]
            
            # 分配
            assignment = self._make_assignment(current_slot, time_slot_id, room_id)
            self._update_used_sets(current_slot, time_slot_id, room_id, True)
            self.assignments.append(assignment)
            
            # 递归求解下一个槽位
            if self._backtrack(slots, index + 1):
                return True
            
            # 回溯
            self.assignments.pop()
            self._update_used_sets(current_slot, time_slot_id, room_id, False)
        
        # 无法分配当前槽位
        self.unassigned.append({
            "course_id": current_slot.course_id,
            "course_name": current_slot.course_name,
            "reason": "No available time slot and room"
        })
        return False
    
    def _make_assignment(self, slot: CourseSlot, time_slot_id: str, room_id: str) -> Assignment:
        """创建分配记录"""
        time_slot = self.time_slots[time_slot_id]
        room = self.classrooms[room_id]
        
        return Assignment(
            course_id=slot.course_id,
            course_name=slot.course_name,
            teacher_id=slot.teacher_id,
            teacher_name=slot.teacher_name,
            class_id=slot.class_id,
            class_name=slot.class_name,
            room_id=room_id,
            room_name=room["name"],
            time_slot_id=time_slot_id,
            day=time_slot["day"],
            period=time_slot["period"],
            time=time_slot["time"]
        )
    
    def _update_used_sets(self, slot: CourseSlot, time_slot_id: str, room_id: str, add: bool):
        """更新占用集合"""
        if add:
            self.teacher_time_used.setdefault(slot.teacher_id, set()).add(time_slot_id)
            self.class_time_used.setdefault(slot.class_id, set()).add(time_slot_id)
            self.room_time_used.setdefault(room_id, set()).add(time_slot_id)
        else:
            self.teacher_time_used.get(slot.teacher_id, set()).discard(time_slot_id)
            self.class_time_used.get(slot.class_id, set()).discard(time_slot_id)
            self.room_time_used.get(room_id, set()).discard(time_slot_id)
    
    def _sort_by_soft_constraints(self, slot: CourseSlot, time_slots: List[str]) -> List[str]:
        """按软约束评分排序时间槽"""
        def calculate_score(time_slot_id: str) -> float:
            score = 0.0
            time_slot = self.time_slots[time_slot_id]
            
            # 教师偏好
            teacher = self.teachers.get(slot.teacher_id, {})
            preferences = teacher.get("preferences", {})
            
            if preferences.get("period") == "morning" and time_slot["period"] <= 4:
                score += 1.0
            elif preferences.get("period") == "afternoon" and time_slot["period"] >= 5:
                score += 1.0
            
            # 课程分布（尽量分散）
            for assignment in self.assignments:
                if assignment.course_id == slot.course_id:
                    # 同一门课的多次排课尽量间隔一天
                    if assignment.day != time_slot["day"]:
                        score += 0.5
            
            return score
        
        time_slots.sort(key=calculate_score, reverse=True)
        return time_slots
    
    def _generate_result(self, source_file: str, success: bool) -> Dict[str, Any]:
        """生成排课结果"""
        # 计算统计信息
        statistics = self._calculate_statistics()
        
        # 确定状态
        if success and not self.unassigned:
            status = "success"
        elif self.unassigned:
            status = "partial"
        else:
            status = "no_solution"
        
        # 转换分配记录为字典
        assignment_dicts = []
        for a in self.assignments:
            assignment_dicts.append({
                "course_id": a.course_id,
                "course_name": a.course_name,
                "teacher_id": a.teacher_id,
                "teacher_name": a.teacher_name,
                "class_id": a.class_id,
                "class_name": a.class_name,
                "room_id": a.room_id,
                "room_name": a.room_name,
                "time_slot_id": a.time_slot_id,
                "day": a.day,
                "period": a.period,
                "time": a.time
            })
        
        return {
            "source_file": source_file,
            "generated_at": datetime.now().isoformat(),
            "status": status,
            "assignments": assignment_dicts,
            "statistics": statistics,
            "unassigned": self.unassigned,
            "warnings": self.warnings
        }
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        total_hours = sum(c.get("hours_per_week", 2) for c in self.courses)
        assigned_hours = len(self.assignments)
        
        # 计算教师满意度
        teacher_satisfaction = {}
        for teacher_id in self.teachers:
            teacher = self.teachers[teacher_id]
            preferences = teacher.get("preferences", {})
            
            if not preferences:
                teacher_satisfaction[teacher_id] = 1.0
                continue
            
            # 计算符合偏好的课时比例
            matching_hours = 0
            total_teacher_hours = 0
            
            for assignment in self.assignments:
                if assignment.teacher_id == teacher_id:
                    total_teacher_hours += 1
                    time_slot = self.time_slots.get(assignment.time_slot_id, {})
                    
                    if preferences.get("period") == "morning" and time_slot.get("period", 0) <= 4:
                        matching_hours += 1
                    elif preferences.get("period") == "afternoon" and time_slot.get("period", 0) >= 5:
                        matching_hours += 1
            
            teacher_satisfaction[teacher_id] = matching_hours / total_teacher_hours if total_teacher_hours > 0 else 1.0
        
        # 计算软约束得分
        soft_constraint_score = sum(teacher_satisfaction.values()) / len(teacher_satisfaction) if teacher_satisfaction else 1.0
        
        return {
            "total_courses": len(self.courses),
            "total_hours": total_hours,
            "assigned_hours": assigned_hours,
            "unassigned_hours": total_hours - assigned_hours,
            "hard_constraint_violations": 0,  # 硬约束必须满足
            "soft_constraint_score": round(soft_constraint_score, 2),
            "teacher_satisfaction": teacher_satisfaction
        }
    
    def validate_schedule(self, schedule: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证排课方案是否满足约束
        
        Args:
            schedule: 排课方案
            constraints: 约束条件
            
        Returns:
            验证结果
        """
        violations = []
        assignments = schedule.get("assignments", [])
        
        # 检查教师冲突
        teacher_time = {}
        for a in assignments:
            key = (a["teacher_id"], a["time_slot_id"])
            if key in teacher_time:
                violations.append({
                    "type": "teacher_conflict",
                    "description": f"Teacher {a['teacher_name']} has conflict at {a['time_slot_id']}"
                })
            teacher_time[key] = True
        
        # 检查班级冲突
        class_time = {}
        for a in assignments:
            key = (a["class_id"], a["time_slot_id"])
            if key in class_time:
                violations.append({
                    "type": "class_conflict",
                    "description": f"Class {a['class_name']} has conflict at {a['time_slot_id']}"
                })
            class_time[key] = True
        
        # 检查教室冲突
        room_time = {}
        for a in assignments:
            key = (a["room_id"], a["time_slot_id"])
            if key in room_time:
                violations.append({
                    "type": "room_conflict",
                    "description": f"Room {a['room_name']} has conflict at {a['time_slot_id']}"
                })
            room_time[key] = True
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "violation_count": len(violations)
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='排课约束求解器')
    parser.add_argument('input', help='约束 JSON 文件路径')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径')
    
    args = parser.parse_args()
    
    solver = ScheduleSolver()
    result = solver.solve(args.input)
    
    # 输出结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
