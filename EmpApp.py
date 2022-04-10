from flask import Flask, render_template, request
from pymysql import connections
from unittest import result
import datetime
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/payroll", methods=['GET', 'POST'])
def Payroll():
    return render_template('PayrollCal.html')


@app.route("/addatt", methods=['GET', 'POST'])
def AddAtt():
    return render_template('AddAtt.html')


@app.route("/getatt", methods=['GET', 'POST'])
def GetAtt():
    return render_template('GetAtt.html')


@app.route("/getpayroll", methods=['GET', 'POST'])
def GetPayroll():

    emp_id = request.form['emp_id']
    day = request.form['noofday']

    cursor = db_conn.cursor()
    select_sql = "SELECT * FROM employee WHERE empid = %s"
    adr = (emp_id, )

    try:
        cursor.execute(select_sql, adr) 

        # if SELECT:
        result = cursor.fetchone()
        
        if result is None:
            return render_template('NullPayroll.html')
        
        dayint = int(day)
        emp_id = result[0]
        name = result[1]
        rate_per_day = result[5]
        salary = rate_per_day * dayint
        
    finally:
        cursor.close()
        
    return render_template('GetPayroll.html', id=emp_id, name=name, rate=rate_per_day, salary=salary)

@app.route("/addatt2", methods=['GET','POST'])
def AddAttOutPut():
    empid = request.form['empid']
    cursor = db_conn.cursor()
    
    now = datetime.datetime.now()
    now.strftime("%d-%m-%Y, %H:%M:%S")

    insert_sql = "INSERT INTO attendance VALUES (%s, %s)"
    cursor = db_conn.cursor()

    if empid == "":
        return "Please enter an Employee ID!"

    try:
        cursor.execute(insert_sql, (empid, now))
        db_conn.commit()

    except Exception as e:
            return str(e)

    finally:
        cursor.close()
    return render_template('AddAttOutPut.html', id=empid, datetime = now)

@app.route("/getatt2", methods=['GET', 'POST'])
def GetAttOutPut():
    empid = request.form['empid']
    cursor = db_conn.cursor()
    cursor.execute('Select * from attendance WHERE empid = %s', empid)
    results = cursor.fetchall()
    lresults = list(results)
    print();
    return render_template('GetAttOutPut.html', results=lresults,)

@app.route("/addemp", methods=['POST'])
def AddEmp():
    empid = request.form['empid']
    name = request.form['name']
    gender = request.form['gender']
    phone = request.form['phone']
    location = request.form['location']
    rate_per_day = request.form['rate_per_day']
    position = request.form['position']
    hire_date = request.form['hire_date']
    image = request.files['image']
    print(type(hire_date))
    conv_rate = int(rate_per_day)
    # print(int(hire_date))
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    # if image.filename == "":
    #     return "Please select a file"

    try:

        cursor.execute(insert_sql, (empid, name, gender, phone,
                       location, conv_rate, position, hire_date))
        db_conn.commit()
        # Uplaod image file in S3 #
        image_name_in_s3 = "empid-" + str(empid) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(
                Key=image_name_in_s3, Body=image)
            bucket_location = boto3.client(
                's3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                image_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=name)


@app.route("/getemp", methods=['GET', 'POST'])
def getEmp():
    return render_template('GetEmp.html')


@app.route("/update/<empid>", methods=['GET', 'POST'])
def updateEmp(empid):

    cursor = db_conn.cursor()
    cursor.execute('Select * from employee WHERE empid = %s', empid)
    results = cursor.fetchall()
    cursor.close()

    return render_template('Edit.html', results=results)


@app.route("/triggerUpdate", methods=['GET', 'POST'])
def triggerUpdate():

    empid = request.form['empid']
    name = request.form['name']
    gender = request.form['gender']
    phone = request.form['phone']
    location = request.form['location']
    rate_per_day = request.form['rate_per_day']
    position = request.form['position']
    hire_date = request.form['hire_date']

    print(type(rate_per_day))

    cursor = db_conn.cursor()
    cursor.execute(
        'UPDATE employee SET name=%s,gender=%s,phone=%s,location=%s,rate_per_day=%s,position=%s,hire_date=%s  WHERE empid=%s',
        (name,
         gender,
         phone,
         location,
         int(rate_per_day),
         position,
         hire_date,
         empid
         )
    )
    db_conn.commit()
    cursor.close()
    print(cursor.rowcount, "record(s) affected")

    return render_template('GetEmpOutput.html')


@app.route("/delete/<empid>", methods=['GET'])
def deleteEmp(empid):
    cursor = db_conn.cursor()
    cursor.execute('DELETE FROM employee WHERE empid = %s', empid)
    db_conn.commit()
    cursor.close()
    return render_template('GetEmpOutput.html')


@app.route("/fetchdata", methods=['GET', 'POST'])
def FetchData():
    cursor = db_conn.cursor()
    cursor.execute('Select * from employee')
    results = cursor.fetchall()
    lresults = list(results)
    cursor.close()

    return render_template(
        'GetEmpOutput.html',
        results=lresults,
    )




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
