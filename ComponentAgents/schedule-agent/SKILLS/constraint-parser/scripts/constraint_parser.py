"""
Constraint Parser - 解析 Markdown 文档中的排课约束条件
将非结构化的排课需求转换为结构化的 JSON 数据
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class ConstraintParser:
    """排课约束解析器"""
    
    # 默认时间槽定义
    DEFAULT_TIME_SLOTS = [
        {"id": "Mon-1", "day": "Monday", "period": 1, "time": "08:00-08:45"},
        {"id": "Mon-2", "day": "Monday", "period": 2, "time": "08:55-09:40"},
        {"id": "Mon-3", "day": "Monday", "period": 3, "time": "10:00-10:45"},
        {"id": "Mon-4", "day": "Monday", "period": 4, "time": "10:55-11:40"},
        {"id": "Mon-5", "day": "Monday", "period": 5, "time": "14:00-14:45"},
        {"id": "Mon-6", "day": "Monday", "period": 6, "time": "14:55-15:40"},
        {"id": "Mon-7", "day": "Monday", "period": 7, "time": "16:00-16:45"},
        {"id": "Mon-8", "day": "Monday", "period": 8, "time": "16:55-17:40"},
        {"id": "Tue-1", "day": "Tuesday", "period": 1, "time": "08:00-08:45"},
        {"id": "Tue-2", "day": "Tuesday", "period": 2, "time": "08:55-09:40"},
        {"id": "Tue-3", "day": "Tuesday", "period": 3, "time": "10:00-10:45"},
        {"id": "Tue-4", "day": "Tuesday", "period": 4, "time": "10:55-11:40"},
        {"id": "Tue-5", "day": "Tuesday", "period": 5, "time": "14:00-14:45"},
        {"id": "Tue-6", "day": "Tuesday", "period": 6, "time": "14:55-15:40"},
        {"id": "Tue-7", "day": "Tuesday", "period": 7, "time": "16:00-16:45"},
        {"id": "Tue-8", "day": "Tuesday", "period": 8, "time": "16:55-17:40"},
        {"id": "Wed-1", "day": "Wednesday", "period": 1, "time": "08:00-08:45"},
        {"id": "Wed-2", "day": "Wednesday", "period": 2, "time": "08:55-09:40"},
        {"id": "Wed-3", "day": "Wednesday", "period": 3, "time": "10:00-10:45"},
        {"id": "Wed-4", "day": "Wednesday", "period": 4, "time": "10:55-11:40"},
        {"id": "Wed-5", "day": "Wednesday", "period": 5, "time": "14:00-14:45"},
        {"id": "Wed-6", "day": "Wednesday", "period": 6, "time": "14:55-15:40"},
        {"id": "Wed-7", "day": "Wednesday", "period": 7, "time": "16:00-16:45"},
        {"id": "Wed-8", "day": "Wednesday", "period": 8, "time": "16:55-17:40"},
        {"id": "Thu-1", "day": "Thursday", "period": 1, "time": "08:00-08:45"},
        {"id": "Thu-2", "day": "Thursday", "period": 2, "time": "08:55-09:40"},
        {"id": "Thu-3", "day": "Thursday", "period": 3, "time": "10:00-10:45"},
        {"id": "Thu-4", "day": "Thursday", "period": 4, "time": "10:55-11:40"},
        {"id": "Thu-5", "day": "Thursday", "period": 5, "time": "14:00-14:45"},
        {"id": "Thu-6", "day": "Thursday", "period": 6, "time": "14:55-15:40"},
        {"id": "Thu-7", "day": "Thursday", "period": 7, "time": "16:00-16:45"},
        {"id": "Thu-8", "day": "Thursday", "period": 8, "time": "16:55-17:40"},
        {"id": "Fri-1", "day": "Friday", "period": 1, "time": "08:00-08:45"},
        {"id": "Fri-2", "day": "Friday", "period": 2, "time": "08:55-09:40"},
        {"id": "Fri-3", "day": "Friday", "period": 3, "time": "10:00-10:45"},
        {"id": "Fri-4", "day": "Friday", "period": 4, "time": "10:55-11:40"},
        {"id": "Fri-5", "day": "Friday", "period": 5, "time": "14:00-14:45"},
        {"id": "Fri-6", "day": "Friday", "period": 6, "time": "14:55-15:40"},
        {"id": "Fri-7", "day": "Friday", "period": 7, "time": "16:00-16:45"},
        {"id": "Fri-8", "day": "Friday", "period": 8, "time": "16:55-17:40"},
    ]
    
    # 星期映射
    DAY_MAP = {
        "周一": "Mon", "星期一": "Mon", "Monday": "Mon", "Mon": "Mon",
        "周二": "Tue", "星期二": "Tue", "Tuesday": "Tue", "Tue": "Tue",
        "周三": "Wed", "星期三": "Wed", "Wednesday": "Wed", "Wed": "Wed",
        "周四": "Thu", "星期四": "Thu", "Thursday": "Thu", "Thu": "Thu",
        "周五": "Fri", "星期五": "Fri", "Friday": "Fri", "Fri": "Fri",
        "周六": "Sat", "星期六": "Sat", "Saturday": "Sat", "Sat": "Sat",
        "周日": "Sun", "星期日": "Sun", "Sunday": "Sun", "Sun": "Sun",
    }
    
    def __init__(self):
        self.teachers = []
        self.courses = []
        self.classrooms = []
        self.classes = []
        self.constraints = {"hard": [], "soft": []}
        self._id_counters = {"teacher": 0, "course": 0, "room": 0, "class": 0}
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一 ID"""
        self._id_counters[prefix] += 1
        return f"{prefix}_{self._id_counters[prefix]:03d}"
    
    def parse(self, md_path: str) -> Dict[str, Any]:
        """
        解析单个 MD 文件
        
        Args:
            md_path: MD 文件路径
            
        Returns:
            结构化的约束数据
        """
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取各部分信息
        teachers = self.extract_teachers(content)
        courses = self.extract_courses(content)
        classrooms = self.extract_classrooms(content)
        classes = self.extract_classes(content)
        constraints = self.extract_constraints(content)
        
        result = {
            "source_file": os.path.basename(md_path),
            "generated_at": datetime.now().isoformat(),
            "teachers": teachers,
            "courses": courses,
            "classrooms": classrooms,
            "classes": classes,
            "time_slots": self.DEFAULT_TIME_SLOTS,
            "constraints": constraints
        }
        
        return result
    
    def parse_batch(self, input_dir: str) -> List[Dict[str, Any]]:
        """
        批量解析目录下所有 MD 文件
        
        Args:
            input_dir: 输入目录路径
            
        Returns:
            解析结果列表
        """
        results = []
        input_path = Path(input_dir)
        
        for md_file in sorted(input_path.glob("*.md")):
            try:
                result = self.parse(str(md_file))
                results.append(result)
            except Exception as e:
                results.append({
                    "source_file": md_file.name,
                    "error": str(e),
                    "status": "failed"
                })
        
        return results
    
    def extract_teachers(self, text: str) -> List[Dict[str, Any]]:
        """
        提取教师信息
        
        支持格式：
        - 表格形式：| 教师姓名 | 可用时间 | 偏好 | 备注 |
        - 列表形式：- 张老师：可用时间 周一1-2节
        """
        teachers = []
        
        # 尝试解析表格
        table_pattern = r'\|\s*(?:教师|老师|姓名).*?\|([\s\S]*?)(?:\n\n|\n#|\Z)'
        table_match = re.search(table_pattern, text)
        
        if table_match:
            table_content = table_match.group(0)
            rows = table_content.strip().split('\n')
            
            # 跳过表头和分隔行
            for row in rows[2:]:
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                if len(cells) >= 1:
                    teacher = {
                        "id": self._generate_id("teacher"),
                        "name": cells[0],
                        "available_slots": self._parse_time_reference(cells[1]) if len(cells) > 1 else ["all"],
                        "preferences": self._parse_preferences(cells[2]) if len(cells) > 2 else {},
                        "group": cells[3] if len(cells) > 3 else ""
                    }
                    teachers.append(teacher)
        
        # 如果表格解析失败，尝试列表形式
        if not teachers:
            list_pattern = r'[-*]\s*(\w+老师|\w+教师)[：:](.*?)(?=\n[-*]|\n\n|\Z)'
            for match in re.finditer(list_pattern, text, re.DOTALL):
                name = match.group(1)
                details = match.group(2)
                
                teacher = {
                    "id": self._generate_id("teacher"),
                    "name": name,
                    "available_slots": self._parse_time_reference(details),
                    "preferences": self._parse_preferences(details),
                    "group": ""
                }
                teachers.append(teacher)
        
        return teachers
    
    def extract_courses(self, text: str) -> List[Dict[str, Any]]:
        """
        提取课程信息
        
        支持格式：
        - 表格形式：| 课程名称 | 课时数 | 授课教师 | 班级 | 连排要求 |
        """
        courses = []
        
        # 尝试解析表格
        table_pattern = r'\|\s*(?:课程|科目).*?\|([\s\S]*?)(?:\n\n|\n#|\Z)'
        table_match = re.search(table_pattern, text)
        
        if table_match:
            table_content = table_match.group(0)
            rows = table_content.strip().split('\n')
            
            for row in rows[2:]:
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                if len(cells) >= 2:
                    course = {
                        "id": self._generate_id("course"),
                        "name": cells[0],
                        "hours_per_week": self._parse_hours(cells[1]) if len(cells) > 1 else 2,
                        "teacher_name": cells[2] if len(cells) > 2 else "",
                        "class_name": cells[3] if len(cells) > 3 else "",
                        "consecutive": self._parse_consecutive(cells[4]) if len(cells) > 4 else 1
                    }
                    courses.append(course)
        
        return courses
    
    def extract_classrooms(self, text: str) -> List[Dict[str, Any]]:
        """
        提取教室信息
        
        支持格式：
        - 表格形式：| 教室编号 | 容量 | 类型 | 可用时间 |
        """
        classrooms = []
        
        # 尝试解析表格
        table_pattern = r'\|\s*(?:教室|课室|房间).*?\|([\s\S]*?)(?:\n\n|\n#|\Z)'
        table_match = re.search(table_pattern, text)
        
        if table_match:
            table_content = table_match.group(0)
            rows = table_content.strip().split('\n')
            
            for row in rows[2:]:
                cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                if len(cells) >= 1:
                    classroom = {
                        "id": self._generate_id("room"),
                        "name": cells[0],
                        "capacity": int(cells[1]) if len(cells) > 1 and cells[1].isdigit() else 50,
                        "type": cells[2] if len(cells) > 2 else "普通教室",
                        "available_slots": self._parse_time_reference(cells[3]) if len(cells) > 3 else ["all"]
                    }
                    classrooms.append(classroom)
        
        return classrooms
    
    def extract_classes(self, text: str) -> List[Dict[str, Any]]:
        """
        提取班级信息（从课程信息中推断）
        """
        classes = []
        class_names = set()
        
        # 从课程信息中提取班级
        courses = self.extract_courses(text)
        for course in courses:
            class_name = course.get("class_name", "")
            if class_name and class_name not in class_names:
                class_names.add(class_name)
                classes.append({
                    "id": self._generate_id("class"),
                    "name": class_name,
                    "size": 45  # 默认班级大小
                })
        
        return classes
    
    def extract_constraints(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        提取约束条件
        
        支持格式：
        ### 硬约束（必须满足）
        1. 同一教师同一时间不能上多门课
        
        ### 软约束（尽量满足）
        1. 张老师 prefer 上午上课
        """
        constraints = {"hard": [], "soft": []}
        
        # 提取硬约束
        hard_pattern = r'(?:硬约束|必须满足).*?\n([\s\S]*?)(?=###|\n#|\Z)'
        hard_match = re.search(hard_pattern, text)
        if hard_match:
            hard_text = hard_match.group(1)
            constraints["hard"] = self._parse_constraint_list(hard_text, "hard")
        
        # 如果没有明确的硬约束部分，添加默认硬约束
        if not constraints["hard"]:
            constraints["hard"] = [
                {"type": "no_teacher_conflict", "description": "同一教师同一时间不能上多门课"},
                {"type": "no_class_conflict", "description": "同一班级同一时间不能上多门课"},
                {"type": "no_room_conflict", "description": "同一教室同一时间不能安排多门课"},
                {"type": "room_capacity", "description": "教室容量必须大于班级人数"}
            ]
        
        # 提取软约束
        soft_pattern = r'(?:软约束|尽量满足).*?\n([\s\S]*?)(?=###|\n#|\Z)'
        soft_match = re.search(soft_pattern, text)
        if soft_match:
            soft_text = soft_match.group(1)
            constraints["soft"] = self._parse_constraint_list(soft_text, "soft")
        
        return constraints
    
    def _parse_time_reference(self, text: str) -> List[str]:
        """
        解析时间引用
        
        支持格式：
        - 周一1-2节, 周三3-4节
        - 周一全天
        - 上午
        - all
        """
        if not text or text.strip().lower() in ["all", "全天", "任意"]:
            return ["all"]
        
        slots = []
        
        # 匹配 周X-Y节 格式
        pattern = r'(周[一二三四五六日]|Mon|Tue|Wed|Thu|Fri|Sat|Sun)[\s]*(\d+)[\s]*[-~到至][\s]*(\d+)[\s]*节?'
        for match in re.finditer(pattern, text):
            day = self.DAY_MAP.get(match.group(1), match.group(1)[:3])
            start = int(match.group(2))
            end = int(match.group(3))
            for period in range(start, end + 1):
                slots.append(f"{day}-{period}")
        
        # 匹配 周X全天 格式
        all_day_pattern = r'(周[一二三四五六日]|Mon|Tue|Wed|Thu|Fri|Sat|Sun)[\s]*全天'
        for match in re.finditer(all_day_pattern, text):
            day = self.DAY_MAP.get(match.group(1), match.group(1)[:3])
            for period in range(1, 9):
                slots.append(f"{day}-{period}")
        
        # 匹配上午/下午
        if "上午" in text:
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                for period in range(1, 5):
                    slots.append(f"{day}-{period}")
        
        if "下午" in text:
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                for period in range(5, 9):
                    slots.append(f"{day}-{period}")
        
        return slots if slots else ["all"]
    
    def _parse_preferences(self, text: str) -> Dict[str, Any]:
        """解析偏好设置"""
        prefs = {}
        
        if not text:
            return prefs
        
        if "上午" in text:
            prefs["period"] = "morning"
        elif "下午" in text:
            prefs["period"] = "afternoon"
        
        return prefs
    
    def _parse_hours(self, text: str) -> int:
        """解析课时数"""
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 2
    
    def _parse_consecutive(self, text: str) -> int:
        """解析连排要求"""
        if not text:
            return 1
        
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        
        if "连排" in text or "连续" in text:
            return 2
        
        return 1
    
    def _parse_constraint_list(self, text: str, constraint_type: str) -> List[Dict[str, Any]]:
        """解析约束列表"""
        constraints = []
        
        pattern = r'(\d+)[.、]\s*(.*?)(?=\n\d+[.、]|\n\n|\Z)'
        for match in re.finditer(pattern, text, re.DOTALL):
            desc = match.group(2).strip()
            
            constraint = {
                "type": self._classify_constraint(desc),
                "description": desc,
                "weight": 1.0 if constraint_type == "hard" else 0.5
            }
            
            # 提取教师偏好
            teacher_match = re.search(r'(\w+老师)\s*(?:prefer|偏好|希望)', desc)
            if teacher_match:
                constraint["teacher_name"] = teacher_match.group(1)
            
            constraints.append(constraint)
        
        return constraints
    
    def _classify_constraint(self, description: str) -> str:
        """根据描述分类约束类型"""
        desc_lower = description.lower()
        
        if "教师" in desc and "冲突" in desc_lower or "同一教师" in desc:
            return "no_teacher_conflict"
        elif "班级" in desc and "冲突" in desc_lower or "同一班级" in desc:
            return "no_class_conflict"
        elif "教室" in desc and "冲突" in desc_lower:
            return "no_room_conflict"
        elif "容量" in desc:
            return "room_capacity"
        elif "上午" in desc or "下午" in desc:
            return "time_preference"
        elif "间隔" in desc or "分布" in desc:
            return "course_distribution"
        else:
            return "custom"


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='解析 MD 文档中的排课约束')
    parser.add_argument('input', help='输入 MD 文件或目录路径')
    parser.add_argument('--output', '-o', help='输出 JSON 文件路径')
    
    args = parser.parse_args()
    
    constraint_parser = ConstraintParser()
    input_path = Path(args.input)
    
    if input_path.is_file():
        result = constraint_parser.parse(str(input_path))
    elif input_path.is_dir():
        results = constraint_parser.parse_batch(str(input_path))
        result = {
            "batch_results": results,
            "total_files": len(results),
            "success_count": sum(1 for r in results if "error" not in r),
            "failed_count": sum(1 for r in results if "error" in r)
        }
    else:
        print(f"Error: {args.input} does not exist")
        return
    
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
