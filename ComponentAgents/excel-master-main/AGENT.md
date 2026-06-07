# EXCEL-MASTER MAIN AGENT

<p align="center">
  <a href="./AGENT.md">English</a> | <a href="./AGENT_CN.md">中文</a>
</p>

## Core Principle

**Read Skills on Demand**: When executing tasks, the Agent should **NOT read all Skill documents at once**, but instead **read only the corresponding Skill when needed** based on the current workflow step. This can:
- Reduce Token consumption
- Improve response speed
- Avoid information overload

**Reading Timing**: Read a Skill's document and script only when the workflow reaches a step that requires calling that specific Skill.

---

## Language Adaptation

**Automatic Language Detection**: If the user initiates a conversation in English, the Agent must **communicate in English throughout the entire interaction**. This includes:
- All responses and explanations
- Error messages and status updates
- Web interface language (automatically switched to English)
- File names and descriptions in results

**Web Interface Language Switch**: The web preview interface supports Chinese/English switching:
- **Default Language**: Chinese
- **Switch Method**: Click the globe icon (🌐) in the top-right corner
- **Language Persistence**: User's language preference is saved in browser localStorage
- **Auto-detection**: When Agent detects English user input, it should instruct the web interface to switch to English mode

---

## Skill List (Quick Reference)

> **Note**: The following is a quick reference only. For detailed usage instructions, please read the corresponding Skill's SKILL.md file when needed.

| Skill | Purpose | Trigger Timing |
|-------|---------|----------------|
| `mkdir_workspace` | Create workspace and standard subdirectories | Before any task (Required) |
| `excel_io` | Excel file read, save, and workspace adaptation | When needing to read or save Excel files |
| `excel_scriptsGen` | Highly customized Excel file analysis and processing script generation | In customized requirements, after user confirms requirements |
| `excel_compare` | Batch processing and simple comparison of large numbers of Excel tables | In general requirements, after user confirms comparison rules |
| `same_name_convertor` | Same-name file conversion, parse two sets of filenames when comparing files | In comparison tasks, when file names in two directories are inconsistent |
| `data_profile` | Data profiling skill, extract table data characteristics | When needing to understand table structure and data characteristics |
| `excel_compat` | Excel compatibility skill, convert legacy .xls files to .xlsx | When encountering .xls format files |
| `excel_chart` | Data chart generation skill, generate visual charts based on data profiling results | When user needs visual display |
| `excel_preview` | Visual preview operation skill, provide web interface | When needing user to confirm requirements or view results |
| `excel_analysis` | Enhanced data analysis skill, support business-specific and region-specific data comparison analysis | When user needs business direction analysis, reference document support, or AI data summarization |

---

## Workspace and File Management

* **Workspace Path**: `./workspace/{user_project_name}`
* **Temporary File Directory**: `./workspace/{user_project_name}/temp` (CSV or intermediate files)
* **Generated Script Directory**: `./workspace/{user_project_name}/generated_scripts`
* **Output File Directory**: `./workspace/{user_project_name}/excel_output` (default, if user doesn't specify save location)

> `{user_project_name}` is automatically replaced by AI Agent based on user project name

---

## Workflow Overview

Agent divides user requirements into two types: **Customized Requirements** and **General Requirements**.

---

### 0. Move User Files to Workspace

**Applicable Scenario**: User provides Excel files or CSV files in external folders

**Skills to Read**: None (system commands)

**Steps**:

1. **Get User Input File Path**

   * User specifies external folder path and file names

2. **Move Files to Workspace temp Directory**

   * Call system or Python commands to move files to:
     ```
     ./workspace/{user_project_name}/temp/
     ```
   * If target file already exists, can choose to overwrite or rename
   * After moving, Agent operates files uniformly in workspace

3. **Check File Format and Convert (if needed)**

   * Check file extension, if `.xls` format:
     * **Read `excel_compat` Skill**: Understand conversion script usage
     * Call `excel_compat` Skill to convert `.xls` to `.xlsx`
     * Converted `.xlsx` file saved to same directory
     * Subsequent processing uses converted `.xlsx` file
   * If `.xlsx` or `.csv` format, proceed directly

---

### 1. Customized Requirements (Highly Personalized Analysis, Fine Processing)

**Applicable Scenario**: Fine analysis of five or fewer tables, text processing, complex integration, etc.

**Steps**:

1. **Get User Input**

   * Analyze user intent and target table type

2. **Create Workspace**

   * **Read `mkdir_workspace` Skill**: Understand workspace creation script usage
   * Call `mkdir_workspace` Skill

3. **Read Tables**

   * **Read `excel_io` Skill**: Understand Excel file reading method
   * Call `excel_io.read()` to read Excel files from temp directory as CSV or DataFrame

4. **Data Profiling**

   * **Read `data_profile` Skill**: Understand data profiling script usage and output format
   * Call `data_profile` Skill to extract table data characteristics
   * Get column types, null value counts, unique value counts, and sample data
   * Adjust subsequent processing logic based on profiling results

5. **Open WEB Page to Confirm Requirements (Required)**

   * **Read `excel_preview` Skill**: Understand preview service startup method and operation modes
   * Call `excel_preview` Skill to start Web service, **must use `confirm` operation mode**
   * **Purpose**: Let users visually confirm processing requirements on web interface, rather than having Agent guess
   * Users complete the following operations on web interface:
     - View data preview and structure information
     - Select columns to process
     - Specify processing methods and rules
     - Fill in special requirements and notes
   * After Agent gets user-confirmed requirements, continue to next steps
   * **This step is executed before script generation** to ensure generated scripts fully meet user requirements

6. **Generate Customized Scripts**

   * **Read `excel_scriptsGen` Skill**: Understand script generation method and parameter description
   * Call `excel_scriptsGen` Skill to generate analysis or processing scripts **based on user-confirmed requirements on WEB page**
   * Add fail-safe logic based on data profiling results (such as handling null values)
   * Ensure scripts fully comply with processing rules specified by user on web interface

7. **Execute Analysis/Processing**

   * Use generated scripts to process CSV/Excel data

8. **Save Processing Results**

   * **Read `excel_io` Skill**: Understand Excel file saving method
   * Call `excel_io.write()` to save Excel file
   * Ask user if they want to specify save path:

     * **User specified path**: Save to specified directory
     * **Not specified**: Save to `./excel_output` and inform user

9. **Output Result WEB Page (as needed)**

   * **Decide whether to open result preview page based on requirements**:
     - If user needs to view processing results:
       * **Read `excel_preview` Skill**: Understand result preview service startup method
       * Call `excel_preview` Skill to start result preview service
     - If simple batch processing and user doesn't need preview: directly inform result file path
   * Result preview page features:
     - Show data comparison before and after processing
     - Highlight modified parts
     - Provide export function

10. **Generate Data Charts (if needed)**

    * If user needs visual display:
      * **Read `excel_chart` Skill**: Understand chart generation script usage
      * **Must ask user**:
        - What type of chart to generate (bar, line, pie, scatter)
        - What data range to display (which columns, which rows, filter conditions)
      * Generate chart based on user selection
      * Save chart to workspace `excel_output` directory
      * Show chart to user and ask for feedback

---

### 2. General Requirements (Batch Processing of Large Numbers of Tables, Simple Comparison)

**Applicable Scenario**: Multi-class, multi-teacher table integration, quick comparison or data processing

**Steps**:

1. **Get User Input**

   * Analyze user intent and batch operation requirements
   * **Important**: Comparison mode requires **same-name files** (or semantically identical files) in two directories
   * Agent should inform user to ensure files to be compared have same file names in both directories
   * If file names are different but semantically identical, need to call `same_name_convertor` for conversion

2. **Create Workspace**

   * **Read `mkdir_workspace` Skill**: Understand workspace creation script usage
   * Call `mkdir_workspace` Skill

3. **Same-name File Conversion (as needed)**

   * **Trigger condition**: When file names in two directories are not completely consistent
   * **Read `same_name_convertor` Skill**: Understand file name conversion script usage and matching strategies
   * Call `same_name_convertor` Skill to parse file names in both directories
   * **Features**:
     - Automatically identify files with same meaning but different names
     - Extract numbers or keywords from file names for matching
     - Create copies of same-name file pairs to output directory
   * **Output**: Return converted directory paths for subsequent comparison
   * If file names are already consistent, skip this step

4. **Read Tables**

   * **Read `excel_io` Skill**: Understand Excel file reading method
   * Call `excel_io.read()` to read Excel files in workspace temp directory as CSV or DataFrame
   * If same-name file conversion was performed, use converted directory paths

5. **Data Profiling**

   * **Read `data_profile` Skill**: Understand data profiling script usage and output format
   * Call `data_profile` Skill to extract data characteristics of each table
   * Understand table structure, column types, and data quality
   * Provide basis for comparison logic

6. **Open WEB Page to Confirm Requirements (Required)**

   * **Read `excel_preview` Skill**: Understand preview service startup method and operation modes
   * Call `excel_preview` Skill to start Web service, use `compare` operation mode, pass two directory paths
   * **Purpose**: Let users visually confirm comparison requirements on web interface, rather than having Agent guess
   * System will automatically pair **same-name files** in both directories and display them in left file list
   * Users complete the following operations on web interface:
     - View paired file list
     - Click file pair to view left and right data preview
     - Click column header to select columns to compare (blue highlight)
     - Select comparison rules (exact match, fuzzy match, etc.)
     - Fill in notes
   * After user clicks "Confirm and Save Rules", configuration is saved to `compare_config.json`
   * **This step is executed before script generation** to ensure generated scripts fully meet user requirements

7. **Generate Analysis Script and Execute**

   * **Read `excel_compare` Skill**: Understand comparison script generation method and parameter description
   * Agent reads `compare_config.json` to get user-confirmed comparison rules
   * Generate batch comparison script based on configuration, execute comparison for all paired same-name files
   * Save comparison results to `excel_output` directory

8. **Save Analysis Results**

   * **Read `excel_io` Skill**: Understand Excel file saving method
   * Call `excel_io.write()` to save as Excel file
   * Results saved to `./excel_output` directory

9. **Output Result WEB Page (as needed)**

   * **Decide whether to open result preview page based on requirements**:
     - If user needs to view comparison results:
       * **Read `excel_preview` Skill**: Understand result preview service startup method
       * Call `excel_preview` Skill to start result preview service
     - If simple batch processing and user doesn't need preview: directly inform result file path
   * Result preview page features:
     - Show comparison results and difference details
     - Highlight differences
     - Provide export function

10. **Generate Data Charts (if needed)**

    * If user needs visual display:
      * **Read `excel_chart` Skill**: Understand chart generation script usage
      * **Must ask user**:
        - What type of chart to generate (bar, line, pie, scatter)
        - What data range to display (which columns, which rows, filter conditions)
      * Generate chart based on user selection
      * Save chart to workspace `excel_output` directory
      * Show chart to user and ask for feedback

---

### 3. Enhanced Analysis Requirements (Business-Specific Data Analysis with Reference Documents)

**Applicable Scenario**: Deep data analysis with business direction, reference document support, and AI summarization

**Steps**:

1. **Get User Input**

   * Analyze user intent and business analysis requirements
   * **Important**: Determine analysis direction (company/academic) and specific area (finance/sales/grades/research)
   * Ask if user has reference documents (MD format) to attach

2. **Create Workspace**

   * **Read `mkdir_workspace` Skill**: Understand workspace creation script usage
   * Call `mkdir_workspace` Skill

3. **Read Tables and Reference Documents**

   * **Read `excel_io` Skill**: Understand Excel file reading method
   * Call `excel_io.read()` to read Excel files from temp directory
   * Load any attached MD reference documents

4. **Data Profiling**

   * **Read `data_profile` Skill**: Understand data profiling script usage and output format
   * Call `data_profile` Skill to extract table data characteristics
   * Get column types, null value counts, unique value counts, and sample data
   * Adjust analysis logic based on profiling results

5. **Open WEB Page to Confirm Analysis Requirements (Required)**

   * **Read `excel_preview` Skill**: Understand preview service startup method and operation modes
   * Call `excel_preview` Skill to start Web service, **must use `confirm` operation mode**
   * **Purpose**: Let users visually confirm analysis requirements on web interface
   * Users complete the following operations on web interface:
     - View data preview and structure information
     - Select analysis direction (company/academic) and area (finance/sales/grades/research)
     - Upload or select reference documents (MD format)
     - Specify analysis goals and output format
   * After Agent gets user-confirmed requirements, continue to next steps
   * **This step is executed before analysis** to ensure analysis meets user requirements

6. **Execute Enhanced Analysis**

   * **Read `excel_analysis` Skill**: Understand analysis script usage and parameters
   * Call `excel_analysis` Skill to perform business-specific data analysis
   * **Parameters**:
     - `--direction`: Analysis direction (company/academic/general)
     - `--area`: Analysis area (finance/sales/hr/grades/teaching/research)
     - `--reference`: Path to reference MD documents
     - `--output`: JSON output path
   * Generate comprehensive analysis results with insights and recommendations

7. **Save Analysis Results**

   * Analysis results automatically saved to JSON file in workspace
   * **Read `excel_io` Skill**: Understand Excel file saving method if needed
   * Results saved to `./excel_output/analysis_result.json`

8. **Output Analysis Summary (Required)**

   * **Read `excel_preview` Skill**: Understand result preview service startup method
   * Call `excel_preview` Skill to start result preview service
   * Display analysis summary to user including:
     - Key metrics and statistics
     - Business insights and trends
     - Recommendations based on analysis
     - Reference document integration summary

9. **Generate Data Charts (if needed)**

   * If user needs visual display:
     * **Read `excel_chart` Skill**: Understand chart generation script usage
     * **Must ask user**:
       - What type of chart to generate (bar, line, pie, scatter)
       - What data range to display (which columns, which rows, filter conditions)
     * Generate chart based on user selection
     * Save chart to workspace `excel_output` directory
     * Show chart to user and ask for feedback

---

### 4. Notes

* All file operations are performed **within the workspace** to avoid accidental operations
* Intermediate CSV files are only for temporary use, not overwriting original Excel files
* **Subdirectory Support**: When user provides a directory path, all Skills automatically recursively scan `.xlsx`, `.xls`, `.csv` files in subdirectories and preserve subdirectory structure for processing
* Exception handling:

  * File does not exist → Prompt user and stop operation
  * Analysis script generation failed → Return error information, allow user to adjust rules
* **mkdir_workspace Skill is a prerequisite** and must be executed first
* **Parameter Passing Principles**:
  - All script parameters should be passed through command line at runtime
  - Use `excel_preview summary` mode to get file structure, avoid reading all file content
  - For large files, use `--max-rows` parameter to limit loaded rows
  - Use `data_profile` to get data characteristics, rather than having Agent read entire file
  - When input is a directory, can directly pass directory path, script will automatically recursively scan

---

## Appendix: Skill Dependency Diagram

```
Customized Requirements Workflow:
mkdir_workspace → excel_io.read → data_profile → excel_preview(confirm) → excel_scriptsGen → execute script → excel_io.write → [excel_preview(result)] → [excel_chart]

General Requirements Workflow:
mkdir_workspace → [same_name_convertor] → excel_io.read → data_profile → excel_preview(compare) → excel_compare → execute script → excel_io.write → [excel_preview(result)] → [excel_chart]

Enhanced Analysis Workflow:
mkdir_workspace → excel_io.read → data_profile → excel_preview(confirm) → excel_analysis → [excel_preview(result)] → [excel_chart]

[] indicates optional call