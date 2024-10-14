from flask import Flask, render_template, request, redirect, url_for, flash
from google.oauth2 import service_account
from googleapiclient.discovery import build
from wtforms import IntegerField, FloatField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, InputRequired
from flask_wtf import FlaskForm
from collections import defaultdict
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv

app = Flask(__name__)
csrf = CSRFProtect(app)

app.config['SECRET_KEY'] = 'vedant363'

# Load environment variables from .env file
load_dotenv()

# Path to your service account key file from environment variable
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

# Define the scopes required for the Google Sheets API (read and write)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Use service account credentials to authenticate
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID of the Google Sheet from the environment variable
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Build the Google Sheets API service
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Specify only the sheet name to dynamically fetch all data
RANGE_NAME = 'sheet1'

# Function to get data from Google Sheets (fetch all data)
def get_data_from_google_sheets():
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        return values
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def get_row_count_from_google_sheets():
    try:
        # Refresh the service to ensure it is aware of new values
        global service, sheet
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        row_count = len(values)  # Get the number of rows
        return row_count
    except Exception as e:
        print(f"Error fetching data: {e}")
        return 0  # Return 0 if an error occurs


# Function to append data to Google Sheets
def append_into_sheet(data):
    try:
        # Prepare the data in the format required by Google Sheets
        body = {'values': [data]}
        
        # Append the data into the sheet
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='sheet1',  # Append to the entire sheet
            valueInputOption="RAW",  # RAW or USER_ENTERED based on your preference
            insertDataOption="INSERT_ROWS",  # Insert new rows at the end
            body=body
        ).execute()
        print(f"Appended {len(data)} rows.")
    except Exception as e:
        print(f"Error appending data: {e}")

# Function to fetch a row from Google Sheets
def fetch_row_data(row_number):
    range_name = f'{RANGE_NAME}!A{row_number}:K{row_number}'  # Adjust range if necessary
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    if values:
        return values[0]
    return None

# Function to update a row in Google Sheets
def update_row_data(row_number, data):
    range_name = f'{RANGE_NAME}!A{row_number}:K{row_number}'  # Adjust range if necessary
    body = {
        'values': [data]
    }
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()


# Function to delete a row in Google Sheets
def delete_row_data(row_number):
    range_name = f'{RANGE_NAME}!A{row_number}:K{row_number}'  # Adjust range if necessary
    result = sheet.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
    ).execute()

# Function to fetch the entire Google Sheet data
def get_sheet_data():
    # Fetch all data from the specified range (entire sheet)
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    
    # Get the rows of data
    rows = result.get('values', [])
    
    return rows




class DiabetesForm(FlaskForm):
    pregnancies = IntegerField('Pregnancies', validators=[InputRequired(), NumberRange(min=0, max=18)])
    glucose = IntegerField('Glucose', validators=[InputRequired(), NumberRange(min=0, max=200)])
    blood_pressure = IntegerField('BloodPressure', validators=[InputRequired(), NumberRange(min=0, max=200)])
    skin_thickness = IntegerField('SkinThickness', validators=[InputRequired(), NumberRange(min=0, max=100)])
    insulin = IntegerField('Insulin', validators=[InputRequired(), NumberRange(min=0, max=1000)])
    bmi = FloatField('BMI', validators=[InputRequired(), NumberRange(min=0.0, max=100.0)])
    diabetes_pedigree_function = FloatField('DiabetesPedigreeFunction', validators=[InputRequired(), NumberRange(min=0.0, max=3.0)])
    age = IntegerField('Age', validators=[InputRequired(), NumberRange(min=20, max=120)])
    outcome = SelectField('Outcome', choices=[(0, 'Negative'), (1, 'Positive')], validators=[DataRequired()])
    submit = SubmitField('Submit')

class UpdateForm(FlaskForm):
    row_number = IntegerField('Row Number', validators=[InputRequired()])
    submit = SubmitField('Update')

    def __init__(self, max_rows=None, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        if max_rows is not None:
            self.row_number.validators.append(NumberRange(min=0, max=max_rows))

class DeleteForm(FlaskForm):
    row_number = IntegerField('Row Number', validators=[InputRequired()])
    submit = SubmitField('Delete')

    def __init__(self, max_rows=None, *args, **kwargs):
        super(DeleteForm, self).__init__(*args, **kwargs)
        if max_rows is not None:
            self.row_number.validators.append(NumberRange(min=0, max=max_rows))

def process_data(values):
    # Initialize a dictionary to count diabetes outcomes by age group
    age_group_count = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        outcome = row[8]     # Index for 'Outcome'
        
        if outcome == '1':  # Assuming Outcome is stored as '1' or '0'
            age_group_count[age_group] += 1

    # Prepare the AgeGroup and Count of Outcome data for Chart.js
    age_groups = list(age_group_count.keys())
    diabetes_counts = list(age_group_count.values())

    return age_groups, diabetes_counts

def process_data2(values):
    # Initialize a dictionary to count diabetes outcomes and total by age group
    age_group_count = defaultdict(int)
    age_group_total = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        outcome = row[8]     # Index for 'Outcome'
        
        age_group_total[age_group] += 1  # Count total people in each age group
        
        if outcome == '1':  # Count diabetic people (Outcome = 1)
            age_group_count[age_group] += 1

    # Prepare AgeGroup, Count of Diabetes, and Total for calculating prevalence
    age_groups = list(age_group_total.keys())
    diabetes_prevalence = [round((age_group_count[age] / age_group_total[age]) * 100, 2) for age in age_groups]

    return age_groups, diabetes_prevalence

def process_insulin_data(values):
    # Initialize dictionaries to sum insulin and count the number of people in each age group
    age_group_insulin_sum = defaultdict(float)
    age_group_count = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        insulin = row[4]     # Index for 'Insulin'
        
        # Skip rows where Insulin is not provided (assuming it's empty or '0')
        if insulin and insulin != '0':
            age_group_insulin_sum[age_group] += float(insulin)
            age_group_count[age_group] += 1

    # Calculate average insulin for each age group
    age_groups = list(age_group_insulin_sum.keys())
    average_insulin = [round(age_group_insulin_sum[age] / age_group_count[age], 2) for age in age_groups]

    return age_groups, average_insulin

def process_blood_pressure_data(values):
    # Initialize dictionaries to sum blood pressure and count the number of people in each age group
    age_group_bp_sum = defaultdict(float)
    age_group_count = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        blood_pressure = row[2]  # Index for 'BloodPressure'
        
        # Skip rows where Blood Pressure is not provided (assuming it's empty or '0')
        if blood_pressure and blood_pressure != '0':
            age_group_bp_sum[age_group] += float(blood_pressure)
            age_group_count[age_group] += 1

    # Calculate average blood pressure for each age group
    age_groups = list(age_group_bp_sum.keys())
    average_blood_pressure = [round(age_group_bp_sum[age] / age_group_count[age], 2) for age in age_groups]

    return age_groups, average_blood_pressure

def process_skin_thickness_data(values):
    # Initialize dictionaries to sum skin thickness and count the number of people in each age group
    age_group_skin_sum = defaultdict(float)
    age_group_count = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        skin_thickness = row[3]  # Index for 'SkinThickness'
        
        # Skip rows where Skin Thickness is not provided (assuming it's empty or '0')
        if skin_thickness and skin_thickness != '0':
            age_group_skin_sum[age_group] += float(skin_thickness)
            age_group_count[age_group] += 1

    # Calculate average skin thickness for each age group
    age_groups = list(age_group_skin_sum.keys())
    average_skin_thickness = [round(age_group_skin_sum[age] / age_group_count[age], 2) for age in age_groups]

    return age_groups, average_skin_thickness

def process_glucose_data(values):
    # Initialize dictionaries to sum glucose and count the number of people in each age group
    age_group_glucose_sum = defaultdict(float)
    age_group_count = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        glucose = row[1]  # Index for 'Glucose'
        
        # Skip rows where Glucose is not provided (assuming it's empty or '0')
        if glucose and glucose != '0':
            age_group_glucose_sum[age_group] += float(glucose)
            age_group_count[age_group] += 1

    # Calculate average glucose for each age group
    age_groups = list(age_group_glucose_sum.keys())
    average_glucose = [round(age_group_glucose_sum[age] / age_group_count[age], 2) for age in age_groups]

    return age_groups, average_glucose

def process_pedigree_function_data(values):
    # Initialize dictionaries to sum diabetes pedigree function and count the number of people in each age group
    age_group_pedigree_sum = defaultdict(float)
    age_group_count = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        age_group = row[9]  # Index for 'AgeGroup'
        diabetes_pedigree_function = row[6]  # Index for 'DiabetesPedigreeFunction'
        
        # Skip rows where Diabetes Pedigree Function is not provided (assuming it's empty or '0')
        if diabetes_pedigree_function and diabetes_pedigree_function != '0':
            age_group_pedigree_sum[age_group] += float(diabetes_pedigree_function)
            age_group_count[age_group] += 1

    # Calculate average Diabetes Pedigree Function for each age group
    age_groups = list(age_group_pedigree_sum.keys())
    average_pedigree_function = [round(age_group_pedigree_sum[age] / age_group_count[age], 2) for age in age_groups]

    return age_groups, average_pedigree_function

def process_avgbmi_data(values):
    # Initialize variables to sum BMI and count the number of entries
    total_bmi = 0.0
    count = 0

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        bmi = row[5]  # Index for 'BMI'
        
        # Skip rows where BMI is not provided (assuming it's empty or '0')
        if bmi and bmi != '0':
            total_bmi += float(bmi)
            count += 1

    # Calculate average BMI
    average_bmi = round(total_bmi / count, 2) if count > 0 else 0

    return average_bmi

def process_avgglucose_data(values):
    # Initialize variables to sum BMI and count the number of entries
    total_glucose = 0.0
    count = 0

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        glucose = row[1]  # Index for 'BMI'
        
        # Skip rows where BMI is not provided (assuming it's empty or '0')
        if glucose and glucose != '0':
            total_glucose += float(glucose)
            count += 1

    # Calculate average BMI
    average_glucose = round(total_glucose / count, 2) if count > 0 else 0

    return average_glucose

def process_avgbp_data(values):
    # Initialize variables to sum BMI and count the number of entries
    total_bp = 0.0
    count = 0

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        bp = row[2]  # Index for 'BMI'
        
        # Skip rows where BMI is not provided (assuming it's empty or '0')
        if bp and bp != '0':
            total_bp += float(bp)
            count += 1

    # Calculate average BMI
    average_bp = round(total_bp / count, 2) if count > 0 else 0

    return average_bp

def process_count(values):
    count = 0
    # Process rows, assuming the first row is the header
    for row in values[1:]:
        bp = row[7]  # Index for 'Pregnancies'
        
        if bp:
            count += 1

    return count

def process_pie_chart_data(values):
    # Initialize a dictionary to count pregnancies where pregnancies > 0 for each outcome
    outcome_counts = defaultdict(int)

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        pregnancies = row[0]  # Index for 'Pregnancies'
        outcome = row[8]      # Index for 'Outcome'
        
        if pregnancies and int(pregnancies) > 0:
            outcome_counts[outcome] += 1

    # Return the count for each outcome
    outcomes = list(outcome_counts.keys())
    pregnancies_counts = [outcome_counts[outcome] for outcome in outcomes]

    return outcomes, pregnancies_counts

def process_stacked_bar_chart_data(values):
    # Initialize a dictionary to count the number of outcomes for each BMIClass
    bmi_class_counts = defaultdict(lambda: {'0': 0, '1': 0})

    # Process rows, assuming the first row is the header
    for row in values[1:]:
        bmi_class = row[10]  # Index for 'BMIClass'
        outcome = row[8]     # Index for 'Outcome'

        if bmi_class and outcome:
            bmi_class_counts[bmi_class][outcome] += 1

    # Convert the dictionary to lists for the chart
    bmi_classes = list(bmi_class_counts.keys())
    outcome_0_counts = [bmi_class_counts[bmi]['0'] for bmi in bmi_classes]
    outcome_1_counts = [bmi_class_counts[bmi]['1'] for bmi in bmi_classes]

    return bmi_classes, outcome_0_counts, outcome_1_counts

# Function to compute AgeGroup
def compute_age_group(age):
    if 20 <= age < 30:
        return '20-30'
    elif 30 <= age < 40:
        return '30-40'
    elif 40 <= age < 50:
        return '40-50'
    elif 50 <= age < 60:
        return '50-60'
    elif 60 <= age < 70:
        return '60-70'
    else:
        return 'Others'

# Function to compute BMIClass
def compute_bmi_class(bmi):
    if bmi < 18.5:
        return 'Underweight'
    elif 18.5 <= bmi < 24.9:
        return 'Healthy'
    elif 25 <= bmi < 29.9:
        return 'Overweight'
    else:
        return 'Obese'
    
def get_sheet_id(spreadsheet_id, sheet_name):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    
    for sheet in sheets:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return None



@app.route('/')
def index():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process all the data for the different charts
    age_groups, diabetes_counts = process_data(values)
    _, diabetes_prevalence = process_data2(values)
    _, avg_insulin = process_insulin_data(values)
    _, avg_blood_pressure = process_blood_pressure_data(values)
    _, avg_skin_thickness = process_skin_thickness_data(values)
    _, avg_glucose = process_glucose_data(values)
    _, avg_pedigree = process_pedigree_function_data(values)

    total_diabetes_count = sum(diabetes_counts)  # Sum of diabetes counts
    average_glucose_count = process_avgglucose_data(values)  # Sum of glucose counts
    average_blood_pressure_count = process_avgbp_data(values)  # Sum of blood pressure counts
    average_bmi_count = process_avgbmi_data(values)
    count = process_count(values)

    outcomes, pregnancies_counts = process_pie_chart_data(values)
    total_pregnancies_count = sum(pregnancies_counts)  # Sum of pregnancies counts
    bmi_classes, outcome_0_counts, outcome_1_counts = process_stacked_bar_chart_data(values)

    # Pass all the processed data to the base.html template
    return render_template('dashboard.html', 
                           age_groups=age_groups,
                           diabetes_counts=diabetes_counts,
                           diabetes_prevalence=diabetes_prevalence,
                           avg_insulin=avg_insulin,
                           avg_blood_pressure=avg_blood_pressure,
                           avg_skin_thickness=avg_skin_thickness,
                           avg_glucose=avg_glucose,
                           avg_pedigree=avg_pedigree,
                           pregnancies_counts=pregnancies_counts,
                           outcomes=outcomes,
                           bmi_classes=bmi_classes,
                           outcome_0_counts=outcome_0_counts,
                           outcome_1_counts=outcome_1_counts,
                           total_diabetes_count=total_diabetes_count,
                           total_pregnancies_count=total_pregnancies_count,
                           average_glucose_count=average_glucose_count,
                           average_blood_pressure_count=average_blood_pressure_count,
                           average_bmi_count=average_bmi_count,
                           count=count)

@app.route('/')
def base():
    return render_template('base.html')

# Route for the form
@app.route('/add', methods=['GET', 'POST'])
def diabetes_form():
    form = DiabetesForm()
    if form.validate_on_submit():
        # Collect data from the form
        age = form.age.data
        bmi = form.bmi.data
        
        # Compute AgeGroup and BMIClass
        age_group = compute_age_group(age)
        bmi_class = compute_bmi_class(bmi)
        
        data = [
            form.pregnancies.data,
            form.glucose.data,
            form.blood_pressure.data,
            form.skin_thickness.data,
            form.insulin.data,
            bmi,
            form.diabetes_pedigree_function.data,
            age,
            form.outcome.data,
            age_group,   # Computed AgeGroup
            bmi_class    # Computed BMIClass
        ]
        
        # Insert the data into Google Sheets
        append_into_sheet(data)
        flash('Data submitted successfully!', 'success')
        return redirect(url_for('base'))

    return render_template('diabetesform.html', form=form)

# Route to update a row
@app.route('/update', methods=['GET', 'POST'])
def update_row():
    row_count = get_row_count_from_google_sheets()  # Call the function to get row count
    form = UpdateForm(max_rows=row_count)  # Pass the row count to the form

    if request.method == 'POST':
        if form.validate_on_submit():  # Validate the form data
            row_number = form.row_number.data  # Access the validated row number
            return redirect(url_for('edit_row', row_number=row_number))
    
    # Render the template with the form if GET or if form validation fails
    return render_template('enter_row_number.html', form=form)


# Route to edit the row data
@app.route('/edit_row/<row_number>', methods=['GET', 'POST'])
def edit_row(row_number):
    row_data = fetch_row_data(row_number)
    
    if not row_data:
        flash('Invalid row number or no data found', 'danger')
        return redirect(url_for('update_row'))

    form = DiabetesForm()

    # Pre-fill form with fetched data
    if request.method == 'GET':
        form.pregnancies.data = int(row_data[0])
        form.glucose.data = int(row_data[1])
        form.blood_pressure.data = int(row_data[2])
        form.skin_thickness.data = int(row_data[3])
        form.insulin.data = int(row_data[4])
        form.bmi.data = float(row_data[5])
        form.diabetes_pedigree_function.data = float(row_data[6])
        form.age.data = int(row_data[7])
        form.outcome.data = int(row_data[8])

    # Update row with modified data
    if form.validate_on_submit():
        age = form.age.data
        bmi = form.bmi.data
        age_group = compute_age_group(age)
        bmi_class = compute_bmi_class(bmi)
        
        data = [
            form.pregnancies.data,
            form.glucose.data,
            form.blood_pressure.data,
            form.skin_thickness.data,
            form.insulin.data,
            bmi,
            form.diabetes_pedigree_function.data,
            age,
            form.outcome.data,
            age_group,
            bmi_class
        ]
        
        # Update the row in Google Sheets
        update_row_data(row_number, data)
        flash('Row updated successfully!', 'success')
        return redirect(url_for('base'))

    return render_template('edit_row.html', form=form, row_number=row_number)

@app.route('/delete', methods=['GET', 'POST'])
def delete_row():
    row_count = get_row_count_from_google_sheets()  # Call the function to get row count
    form = DeleteForm(max_rows=row_count)  # Pass the row count to the form

    if request.method == 'POST':
        if form.validate_on_submit():  # Validate the form data
            row_number = form.row_number.data  # Access the validated row number
            # Example usage
            delete_row_data(row_number)  # Deletes the 5th row
            flash('Row deleted successfully!', 'success')
            return redirect(url_for('base'))
    
    # Render the template with the form if GET or if form validation fails
    return render_template('delete_row_number.html', form=form)

@app.route('/view')
def view_sheet():
    # Fetch the Google Sheet data
    sheet_data = get_sheet_data()

    # Add a row number as the first column (skip the header row)
    for idx, row in enumerate(sheet_data[1:], start=1):  # Skip header, start from 1
        row.insert(0, idx)  # Insert the row number at the beginning of each row

    # Add "Row Number" to the header
    sheet_data[0].insert(0, "Row Number")

    # Pass the updated sheet data to the HTML template
    return render_template('view_sheet.html', sheet_data=sheet_data)



@app.route('/d')
def index2():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate diabetes prevalence by age group
    age_groups, diabetes_prevalence = process_data2(values)

    # Pass data to the template for prevalence chart
    return render_template('diabetesprevalence.html', age_groups=age_groups, diabetes_prevalence=diabetes_prevalence)

@app.route('/a')
def average_insulin():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate average insulin by age group
    age_groups, avg_insulin = process_insulin_data(values)

    # Pass data to the template for the average insulin chart
    return render_template('insulinbyagegroup.html', age_groups=age_groups, avg_insulin=avg_insulin)

@app.route('/b')
def average_blood_pressure():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate average blood pressure by age group
    age_groups, avg_blood_pressure = process_blood_pressure_data(values)

    # Pass data to the template for the average blood pressure chart
    return render_template('averagebloodpressure.html', age_groups=age_groups, avg_blood_pressure=avg_blood_pressure)

@app.route('/s')
def average_skin_thickness():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate average skin thickness by age group
    age_groups, avg_skin_thickness = process_skin_thickness_data(values)

    # Pass data to the template for the average skin thickness chart
    return render_template('averageskinthickness.html', age_groups=age_groups, avg_skin_thickness=avg_skin_thickness)

@app.route('/g')
def average_glucose():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate average glucose by age group
    age_groups, avg_glucose = process_glucose_data(values)

    # Pass data to the template for the average glucose chart
    return render_template('averageglucose.html', age_groups=age_groups, avg_glucose=avg_glucose)


@app.route('/p')
def average_pedigree():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate average diabetes pedigree function by age group
    age_groups, avg_pedigree = process_pedigree_function_data(values)

    # Pass data to the template for the average pedigree chart
    return render_template('averagepedigree.html', age_groups=age_groups, avg_pedigree=avg_pedigree)

@app.route('/pr')
def pregnancies_pie():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate the count of pregnancies where pregnancies > 0, grouped by outcome
    outcomes, pregnancies_counts = process_pie_chart_data(values)

    # Pass data to the template for pie chart
    return render_template('pregnanciespie.html', outcomes=outcomes, pregnancies_counts=pregnancies_counts)

@app.route('/st')
def stacked_bar():
    # Get data from Google Sheets
    values = get_data_from_google_sheets()

    # Process data to calculate the count of outcomes by BMIClass
    bmi_classes, outcome_0_counts, outcome_1_counts = process_stacked_bar_chart_data(values)

    # Pass data to the template for stacked bar chart
    return render_template('stackedbar.html', bmi_classes=bmi_classes, outcome_0_counts=outcome_0_counts, outcome_1_counts=outcome_1_counts)

if __name__ == '__main__':
    app.run(debug=True)
