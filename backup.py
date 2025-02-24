import os
from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        room_number = request.form.get('room_number')
        max_capacity = int(request.form.get('max_capacity'))
        
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            
            # ตรวจสอบและแปลง Timestamp
            if 'Timestamp (s)' not in df.columns:
                return "ไม่พบคอลัมน์ 'Timestamp (s)' ในไฟล์ CSV"
            df['Timestamp'] = pd.to_datetime(df['Timestamp (s)'], unit='s', errors='coerce')
            
            # แปลง Object Details เป็น DataFrame ใหม่
            records = []
            for _, row in df.iterrows():
                time = row['Timestamp']
                objects = str(row['Object Details']).split(', ')
                for obj in objects:
                    if ': ' in obj:
                        name, count = obj.split(': ')
                        records.append({'Timestamp': time, 'Object': name, 'Count': int(count)})
            
            object_df = pd.DataFrame(records)
            
            # ดึงข้อมูลเฉพาะ 'person'
            person_df = object_df[object_df['Object'] == 'person']
            
            # สร้างกราฟเส้น (Line Chart) สำหรับจำนวนคน
            line_fig = px.line(person_df, x='Timestamp', y='Count', title='Person Count (คน)', markers=True)
            line_graph_html = to_html(line_fig, full_html=False)
            
            # คำนวณค่าสูงสุดของแต่ละ Object
            max_counts = object_df.groupby('Object')['Count'].max().reset_index()
            
            # สร้าง Pie Chart โดยใช้ค่าที่สูงสุดของแต่ละ Object
            pie_fig = px.pie(max_counts, names='Object', values='Count', 
                             title='Object Distribution Percentage (Max Value)', color_discrete_sequence=px.colors.qualitative.Set3)
            pie_graph_html = to_html(pie_fig, full_html=False)
            
            # คำนวณ Room Utilization Rate
            max_people = person_df['Count'].max() if not person_df.empty else 0
            utilization_rate = round((max_people / max_capacity) * 100, 2) if max_capacity > 0 else 0
            
            # สร้าง Gauge Chart แสดงเปอร์เซ็นต์ของการใช้งานห้อง
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=utilization_rate,
                title={'text': "Room Utilization Rate (%)"},
                gauge={'axis': {'range': [0, 100]},  # แสดงค่าเป็นเปอร์เซ็นต์ 0-100
                       'bar': {'color': "blue"},
                       'steps': [
                           {'range': [0, 100], 'color': "lightgray"}]}  # สีของบาร์ตามค่าเปอร์เซ็นต์
            ))
            gauge_graph_html = to_html(gauge_fig, full_html=False)
            
            return render_template('dashboard.html', 
                                   room_name=room_name,
                                   room_number=room_number,
                                   max_capacity=max_capacity,
                                   utilization_rate=utilization_rate,
                                   max_people=max_people,  # เพิ่มข้อมูลจำนวนคน
                                   line_graph_html=line_graph_html,
                                   pie_graph_html=pie_graph_html,
                                   gauge_graph_html=gauge_graph_html)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
