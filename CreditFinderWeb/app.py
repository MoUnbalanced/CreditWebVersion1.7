import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# Page config
st.set_page_config(
    page_title="Credit Class Finder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00d9ff;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0, 217, 255, 0.3);
    }
    .stAlert {
        background-color: rgba(0, 217, 255, 0.1);
        border-left: 4px solid #00d9ff;
    }
    .result-box {
        background-color: #1a1a2e;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #00ff9f;
        margin: 10px 0;
    }
    .credit-class {
        background-color: rgba(0, 255, 159, 0.05);
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #00ff9f;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #888;
        border-top: 1px solid #333;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">⚡ STUDENT CREDIT CLASS FINDER ⚡</h1>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if 'classes_df' not in st.session_state:
    st.session_state.classes_df = None
if 'students_df' not in st.session_state:
    st.session_state.students_df = None
if 'last_results' not in st.session_state:
    st.session_state.last_results = None
if 'message_data' not in st.session_state:
    st.session_state.message_data = None

# Sidebar for file uploads
with st.sidebar:
    st.header("📂 Upload Files")
    
    classes_file = st.file_uploader(
        "Upload Classes File",
        type=['xlsx', 'xls'],
        help="Excel file containing class information"
    )
    
    students_file = st.file_uploader(
        "Upload Students File",
        type=['xlsx', 'xls'],
        help="Excel file containing student enrollments"
    )
    
    if classes_file and students_file:
        if st.button("⚡ Load Files", type="primary", use_container_width=True):
            with st.spinner("Loading files..."):
                try:
                    st.session_state.classes_df = pd.read_excel(classes_file)
                    st.session_state.students_df = pd.read_excel(students_file)
                    st.success("✅ Files loaded successfully!")
                    st.info(f"📊 {len(st.session_state.classes_df)} classes | {len(st.session_state.students_df)} enrollments")
                except Exception as e:
                    st.error(f"Error loading files: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 💡 About")
    st.info("This tool helps find suitable credit classes for students based on their schedule and subjects.")

# Main content
if st.session_state.classes_df is not None and st.session_state.students_df is not None:
    
    # Search section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Search for Student (Name or ID)",
            placeholder="Enter student name or ID...",
            key="search_input"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        process_all = st.checkbox("Process All Students")
    
    # Missed class section
    missed_class_id = st.text_input(
        "🎯 Missed Class ID (Optional)",
        placeholder="Leave blank for general credits, or enter ClassID for replacements",
        help="Enter a specific ClassID to find replacement classes"
    )
    
    # Search button
    if st.button("🔎 Find Credit Classes", type="primary", use_container_width=True):
        if not search_term and not process_all:
            st.warning("⚠️ Please enter a student name/ID or check 'Process All Students'")
        else:
            with st.spinner("Processing..."):
                try:
                    results, student_name, subject, credit_classes = find_credit_classes(
                        st.session_state.classes_df,
                        st.session_state.students_df,
                        search_term if not process_all else None,
                        missed_class_id if missed_class_id else None,
                        process_all
                    )
                    
                    st.session_state.last_results = results
                    st.session_state.message_data = {
                        'student_name': student_name,
                        'subject': subject,
                        'credit_classes': credit_classes
                    }
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display results
    if st.session_state.last_results:
        st.markdown("---")
        st.markdown("### 📊 Results")
        
        # Display results in formatted boxes
        for result_section in st.session_state.last_results:
            if result_section['type'] == 'student_info':
                st.markdown(f"""
                <div class="result-box">
                    <h3 style="color: #00d9ff; margin: 0;">👤 {result_section['name']}</h3>
                    <p style="color: #888; margin: 5px 0;">ID: {result_section['id']} | Year: {result_section['year']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if result_section.get('note'):
                    st.info(result_section['note'])
                
            elif result_section['type'] == 'credit_classes':
                if result_section['classes']:
                    st.success(f"✅ Found {len(result_section['classes'])} credit class(es)")
                    
                    for i, cls in enumerate(result_section['classes'], 1):
                        st.markdown(f"""
                        <div class="credit-class">
                            <strong>[{i}] {cls['subject']} (Stream {cls['stream']})</strong> - {cls['ability']}<br>
                            📅 {cls['day']} @ {cls['time']} | 🆔 ClassID: {cls['class_id']}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ No classes available to be credits")
        
        # Export and message buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Export to text
            results_text = format_results_for_export(st.session_state.last_results)
            st.download_button(
                label="💾 Export Results",
                data=results_text,
                file_name=f"credit_classes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Copy message template
            if st.session_state.message_data and missed_class_id:
                if st.button("📋 Copy Message Template", use_container_width=True):
                    message = generate_message_template(st.session_state.message_data)
                    st.text_area("Message Template (Copy this)", message, height=200)

else:
    # Welcome screen
    st.info("👆 Please upload both Excel files in the sidebar to get started!")
    
    with st.expander("📖 How to use"):
        st.markdown("""
        1. **Upload Files**: Upload your Classes and Students Excel files in the sidebar
        2. **Load Files**: Click the "Load Files" button
        3. **Search**: Enter a student name or ID, or check "Process All"
        4. **Optional**: Enter a Missed Class ID to find replacements
        5. **Find Classes**: Click "Find Credit Classes"
        6. **Export**: Download results or copy message template
        """)
    
    with st.expander("ℹ️ Rules Applied"):
        st.markdown("""
        - Classes must be in the **same year** as the student
        - Only **Group classes** with **Active status** are shown
        - Classes must be at times when **student is free**
        - If student has **both Stream A & B** of a subject:
          - Priority 1: Different subjects (same ability)
          - Priority 2: Same subject (different ability)
        - Otherwise:
          - Same subject, different stream or ability
        """)

# Footer
st.markdown("""
<div class="footer">
    <p>© 2025 Credit Class Finder | Developed by Mohammed Abdelwahed | Version 1.7.2</p>
    <p style="font-size: 0.8rem;">All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)


# Helper Functions
def find_credit_classes(classes_df, students_df, search_term, missed_class_id, process_all):
    """Main logic for finding credit classes"""
    results = []
    message_student_name = None
    message_subject = None
    message_credit_classes = []
    
    # Detect columns
    student_id_col = next((col for col in students_df.columns if 'student' in col.lower() and 'id' in col.lower()), None)
    student_name_col = next((col for col in students_df.columns if 'student' in col.lower() and 'name' in col.lower()), None)
    class_id_col = next((col for col in students_df.columns if 'class' in col.lower() and 'id' in col.lower()), None)
    year_col = next((col for col in students_df.columns if 'year' in col.lower()), None)
    time_col = next((col for col in students_df.columns if 'time' in col.lower()), None)
    
    class_id_col_classes = next((col for col in classes_df.columns if 'class' in col.lower() and 'id' in col.lower()), None)
    subject_col = next((col for col in classes_df.columns if 'subject' in col.lower()), None)
    stream_col = next((col for col in classes_df.columns if 'stream' in col.lower()), None)
    ability_col = next((col for col in classes_df.columns if 'ability' in col.lower()), None)
    year_col_classes = next((col for col in classes_df.columns if 'year' in col.lower()), None)
    time_col_classes = next((col for col in classes_df.columns if 'time' in col.lower()), None)
    day_col = next((col for col in classes_df.columns if 'day' in col.lower()), None)
    classtype_col = next((col for col in classes_df.columns if 'type' in col.lower()), None)
    status_col = next((col for col in classes_df.columns if 'status' in col.lower()), None)
    duration_col = next((col for col in classes_df.columns if 'duration' in col.lower()), None)
    
    # Filter students
    if process_all:
        student_ids = students_df[student_id_col].unique()
    else:
        filtered = students_df[
            (students_df[student_id_col].astype(str).str.contains(search_term, case=False, na=False)) |
            (students_df[student_name_col].astype(str).str.contains(search_term, case=False, na=False))
        ]
        student_ids = filtered[student_id_col].unique()
    
    # Process each student
    for student_id in student_ids:
        student_classes = students_df[students_df[student_id_col] == student_id].copy()
        
        if student_classes.empty:
            continue
        
        student_info = student_classes.iloc[0]
        student_name = str(student_info[student_name_col]) if pd.notna(student_info.get(student_name_col)) else "Unknown"
        student_year = student_info[year_col] if pd.notna(student_info.get(year_col)) else "Unknown"
        
        if message_student_name is None:
            message_student_name = student_name
        
        # Get enrolled classes and times
        enrolled_classes = []
        enrolled_times = []
        
        for idx in student_classes.index:
            class_val = student_classes.loc[idx, class_id_col]
            if pd.notna(class_val):
                enrolled_classes.append(class_val)
            
            if time_col:
                time_val = student_classes.loc[idx, time_col]
                if pd.notna(time_val):
                    enrolled_times.append(time_val)
        
        # Track subject/stream/ability map
        subject_stream_ability_map = {}
        student_all_abilities = set()
        
        for idx in student_classes.index:
            class_id = student_classes.loc[idx, class_id_col]
            if pd.isna(class_id):
                continue
            
            class_info = classes_df[classes_df[class_id_col_classes] == class_id]
            if not class_info.empty:
                subject = class_info.iloc[0][subject_col]
                stream = class_info.iloc[0][stream_col]
                ability = class_info.iloc[0][ability_col]
                
                if pd.notna(subject) and pd.notna(stream) and pd.notna(ability):
                    if subject not in subject_stream_ability_map:
                        subject_stream_ability_map[subject] = {}
                    if stream not in subject_stream_ability_map[subject]:
                        subject_stream_ability_map[subject][stream] = set()
                    
                    subject_stream_ability_map[subject][stream].add(ability)
                    student_all_abilities.add(ability)
        
        # Find subjects with both streams
        subjects_with_both_streams = set()
        for subject, streams in subject_stream_ability_map.items():
            if len(streams) >= 2:
                subjects_with_both_streams.add(subject)
        
        # Get available classes
        if classtype_col and status_col:
            available_classes = classes_df[
                (classes_df[year_col_classes] == student_year) &
                (classes_df[classtype_col].notna()) &
                (classes_df[classtype_col].astype(str).str.lower() == 'group') &
                (classes_df[status_col].notna()) &
                (classes_df[status_col].astype(str).str.lower() == 'active')
            ].copy()
        else:
            available_classes = classes_df[classes_df[year_col_classes] == student_year].copy()
        
        # Find credit classes
        credit_classes = []
        
        for idx in available_classes.index:
            available_class = available_classes.loc[idx]
            class_id = available_class[class_id_col_classes]
            
            if pd.isna(class_id) or class_id in enrolled_classes:
                continue
            
            # Check time conflict
            if time_col_classes:
                class_time = available_class[time_col_classes]
                if pd.notna(class_time) and class_time in enrolled_times:
                    continue
            
            subject = available_class[subject_col]
            stream = available_class[stream_col]
            ability = available_class[ability_col]
            
            if pd.isna(subject) or pd.isna(stream) or pd.isna(ability):
                continue
            
            # Apply logic based on whether student has both streams
            is_valid = False
            
            if subjects_with_both_streams:
                # Different subject with same ability (priority 1)
                if subject not in subjects_with_both_streams and ability in student_all_abilities:
                    is_valid = True
                # Same subject with different ability (priority 2)
                elif subject in subjects_with_both_streams:
                    subject_abilities = set()
                    for stream_abilities in subject_stream_ability_map[subject].values():
                        subject_abilities.update(stream_abilities)
                    if ability not in subject_abilities:
                        is_valid = True
            else:
                # Normal logic
                if subject in subject_stream_ability_map:
                    student_streams = set(subject_stream_ability_map[subject].keys())
                    if stream not in student_streams:
                        is_valid = True
                    elif stream in subject_stream_ability_map[subject]:
                        if ability not in subject_stream_ability_map[subject][stream]:
                            is_valid = True
                else:
                    is_valid = True
            
            if is_valid:
                # Format time
                time_display = "N/A"
                if time_col_classes and pd.notna(available_class.get(time_col_classes)):
                    try:
                        start_time = available_class[time_col_classes]
                        if isinstance(start_time, str):
                            start_time = datetime.strptime(start_time, "%H:%M:%S").time()
                        
                        if hasattr(start_time, 'hour'):
                            duration_minutes = 60
                            if duration_col and pd.notna(available_class.get(duration_col)):
                                duration_minutes = int(available_class[duration_col])
                            
                            start_dt = datetime.combine(datetime.today(), start_time)
                            end_dt = start_dt + timedelta(minutes=duration_minutes)
                            time_display = f"{start_dt.strftime('%I:%M %p').lstrip('0')} - {end_dt.strftime('%I:%M %p').lstrip('0')}"
                    except:
                        time_display = str(available_class[time_col_classes])
                
                credit_classes.append({
                    'class_id': str(available_class[class_id_col_classes]),
                    'subject': str(available_class[subject_col]),
                    'stream': str(available_class[stream_col]).upper(),
                    'ability': str(available_class[ability_col]).title(),
                    'day': str(available_class[day_col]).title() if day_col and pd.notna(available_class.get(day_col)) else "N/A",
                    'time': time_display
                })
                
                message_credit_classes.append({
                    'day': str(available_class[day_col]).title() if day_col and pd.notna(available_class.get(day_col)) else "N/A",
                    'time': time_display,
                    'subject': str(available_class[subject_col]),
                    'stream': str(available_class[stream_col]).upper(),
                    'ability': str(available_class[ability_col]).title()
                })
        
        # Add to results
        note = None
        if subjects_with_both_streams:
            note = f"📌 Student has BOTH Stream A and Stream B in: {', '.join(subjects_with_both_streams)}"
        
        results.append({
            'type': 'student_info',
            'name': student_name,
            'id': student_id,
            'year': student_year,
            'note': note
        })
        
        results.append({
            'type': 'credit_classes',
            'classes': credit_classes
        })
    
    return results, message_student_name, message_subject, message_credit_classes


def format_results_for_export(results):
    """Format results as plain text for export"""
    text = "CREDIT CLASS FINDER - RESULTS\n"
    text += "=" * 80 + "\n\n"
    
    for section in results:
        if section['type'] == 'student_info':
            text += f"Student: {section['name']} (ID: {section['id']}) - Year {section['year']}\n"
            text += "-" * 80 + "\n"
            if section.get('note'):
                text += f"{section['note']}\n\n"
        
        elif section['type'] == 'credit_classes':
            if section['classes']:
                text += f"Available Credit Classes: {len(section['classes'])}\n\n"
                for i, cls in enumerate(section['classes'], 1):
                    text += f"  [{i}] {cls['subject']} (Stream {cls['stream']}) - {cls['ability']}\n"
                    text += f"      {cls['day']} @ {cls['time']} | ClassID: {cls['class_id']}\n\n"
            else:
                text += "No classes available to be credits\n\n"
        
        text += "\n"
    
    return text


def generate_message_template(data):
    """Generate message template"""
    student_name = data['student_name']
    subject = data['subject']
    credit_classes = data['credit_classes']
    
    options = [f"{cls['day']} at {cls['time']}" for cls in credit_classes]
    
    if len(options) == 1:
        options_str = options[0]
    elif len(options) == 2:
        options_str = f"{options[0]} or {options[1]}"
    else:
        options_str = ", ".join(options[:-1]) + f", or {options[-1]}"
    
    message = f"""This is regarding {student_name}'s cancelled {subject} lesson on Christmas Day. We'd like to arrange a replacement class for them on {options_str}. Please let us know if this works for you, and we'll happily book it in.

Best regards,"""
    
    return message