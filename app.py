import os
import numpy as np
import cv2
import face_recognition
from flask_pymongo import PyMongo,pymongo
import gridfs
from http import HTTPStatus
import codecs
import base64
from flask import Flask, render_template, redirect, url_for, request, session, flash
import bcrypt
from datetime import date
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
app=Flask(__name__)
app.config['MONGO_URI']="mongodb://localhost:27017/attendance-system"
mongo=PyMongo(app)
grid_fs=gridfs.GridFS(mongo.db)
ALLOWED_EXTENSIONS=set(['png','jpg','jpeg','gif'])
num=0

@app.route('/getCourse', methods=['POST','GET'])
def getCourse():
 if 'role' in session:
    if session.get('role')=='admin':
     if request.method == 'GET':
      course_list = []
      offset = 0
      limit = 5
      faculty_code = request.args.get('faculty')
      faculty=''
      year = request.args.get('year')
      semester =request.args.get('semester')
      department_code=request.args.get('department')
      department=''
      faculty=findFaculity(faculty_code)
      if (department_code == "ENGT"):
        department = 'school of engineering and techonology'
        print(department)
      if year is  None:
        count = mongo.db.course.find({'active':True}).count()
        if count!=0:
         myCursor = mongo.db.course
         if request.args.get('offset'):
            offset = int(request.args['offset'])
            limit = int(request.args['limit'])
         next = offset + limit
         previous = offset - limit
         starting_id = myCursor.find({'active':True}).sort('_id', pymongo.ASCENDING)
         last_id = starting_id[offset]['_id']
         course_cursor = myCursor.find({'_id': {'$gte': last_id},'active':True}).sort('_id', pymongo.ASCENDING).limit(limit)
         for course in course_cursor:
            course_list.append(course)
         if (offset + 1 == offset + len(course_list)):
            items = 'Showing ' + str(offset + 1) + ' of ' + str(count) + ' Entries'
         else:
            items = 'Showing ' + str(offset + 1) + ' to ' + str(offset + len(course_list)) + ' of ' + str(
                count) + ' Entries'


         return render_template('course.html',username=session['username'],
                           courses=course_list,
                           next=next,
                           previous=previous,
                           total=count,
                           entries=items)
        else:
            flash("Oops! courses unit cannot be found,have you added any course?")
            return render_template('course.html', username=session['username'])

      else:
        count = mongo.db.course.find({'faculty':faculty,'department':department,'year':year,'semester':semester,'active':True}).count()
        if count!=0:
         myCursor = mongo.db.course
         if request.args.get('offset'):
            offset = int(request.args['offset'])
            limit = int(request.args['limit'])
         next = offset + limit
         previous = offset - limit
         starting_id = myCursor.find({'faculty':faculty,'department':department,'year':year,'semester':semester,'active':True}).sort('_id', pymongo.ASCENDING)
         last_id = starting_id[offset]['_id']
         course_cursor = myCursor.find({'_id': {'$gte': last_id},'faculty':faculty,'department':department,'year':year,'semester':semester,'active':True}).sort('_id', pymongo.ASCENDING).limit(limit)
         for course in course_cursor:
            course_list.append(course)
         if (offset + 1 == offset + len(course_list)):
            items = 'Showing ' + str(offset + 1) + ' of ' + str(count) + ' Entries'
         else:
            items = 'Showing ' + str(offset + 1) + ' to ' + str(offset + len(course_list)) + ' of ' + str(
                count) + ' Entries'
         year=int(year)
         return render_template('course.html', username=session['username'],
                               courses=course_list,
                               next=next,
                               previous=previous,
                               total=count,
                               entries=items,
                               faculty=faculty_code,
                               department=department_code,
                               year=year,
                               semester=semester

                               )
        else:
            flash("Oops! It seems this course unit cannot be found" )
            return render_template('course.html', username=session['username'])
    else:
        return render_template('login.html')
 else:
     return render_template('login.html')

   #admin routes
@app.route('/addCourse',methods=['POST','GET'])
def addCourse():
 if 'role' in session:
   if session.get('role') == 'admin':
      if request.method == 'POST':
       unit_desc = request.form.get('unit_desc')
       type=request.form.get('type')
       faculty_code = request.form.get('faculty')
       department=request.form.get('department')

       year=request.form.get('year')
       semester=request.form.get('semester')
       faculty=findFaculity(faculty_code)
       if (department =="ENGT"):
           department='school of engineering and techonology'
       count = mongo.db.course.find({'faculty':faculty,'department':department,'year':year,'semester':semester,'type':type}).count()
       code= str(year)+str(semester)+str(count)
       course_code = type + " " + str(year) + str(semester) + str(count)
       course={'type':type,'code':code,'course_code':course_code,'description':unit_desc,'department':department,'faculty':faculty,'year':year,'semester':semester,'active':True}
       mongo.db.course.insert(course)
       flash(" You have successfully added, " + unit_desc + ", the code for this unit is, " + course_code)
       return render_template('add-course.html', username=session['username']),HTTPStatus.CREATED
      else:
        return render_template('add-course.html',username=session['username'])
   else:
       return render_template('login.html')
 else:
     return render_template('login.html')

@app.route('/addStudent',methods=['POST'])
def addStudent():
 if 'role' in session:
   if session.get('role') == 'admin':
    if request.method == 'POST':
        first_name=request.form.get('first_name')
        last_name = request.form.get("last_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        mode = request.form['mode']
        course = request.form['course']
        course_desc =findFaculity(course)
        count = mongo.db.student.find({'course':course_desc}).count()
        if(count==0):
            reg_num=1
        else:
            reg_num=count+1
        today = date.today()
        today=str(today)
        datelist=today.split('-')
        print(datelist)
        year=datelist[0]
        month=datelist[1]
        year=year[2]+year[3]
        reg=course+"/"+mode+"/"+str(reg_num)+"/"+month+"/"+year
        print(reg)
        name=first_name+" "+last_name

        student_mode=findMode(mode)
        print(course)
        hash_password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        student={'name':name,"reg":reg,"course":course_desc,"mode":student_mode,"year of reg":today,"password":hash_password,'active':True,'profile_url':""}
        mongo.db.student.insert(student)


        flash(" you have successfully added " + name + " is Registration number is " + reg)
        return render_template('user-edit.html', username=session['username'])
   else:
       return render_template('login.html')
 else:
     return render_template('login.html')

@app.route('/addLecturer',methods=['POST'])
def addLecturer():
 if 'role' in session:
   if session.get('role') == 'admin':
    first_name = request.form.get('first_name')
    last_name = request.form.get("last_name")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    mode = request.form['mode']
    department = request.form['department']
    faculty=request.form.get('faculty')
    faculty_desc=findFaculity(faculty)
    teaching_mode=find_lec_mode(mode)
    if (department == "ENGT"):
        department_desc = "School of Science Engineering and Technology"
    elif (department == "EDU"):
        department_desc = "School of Education"

    count = mongo.db.lecturers .find({'department': department_desc}).count()
    print(count)
    if (count == 0):
        reg_num = 1
    else:
        reg_num = count + 1
    today = date.today()
    print(today)
    year = str(today.year)
    month = str(today.month)
    year = year[2] + year[3]
    staff_number = department + "/" + mode + "/" + str(reg_num) + "/" + month + "/" + year
    name = first_name + " " + last_name
    today = str(today)
    print(today)
    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    lecture={'name':name,"staff_num":staff_number,'mode':teaching_mode,'faculty':faculty_desc,'department':department_desc,"reg_date":today,"password":hash_password,'active':True}
    print(lecture)
    mongo.db.lecturers.insert(lecture)
    flash (" you have successfully added "+name+ " is staff number is " + staff_number)
    return render_template('lecturer-edit.html', username=session['username'])
   else:
       return render_template('login.html')
 else:
     return render_template('login.html')

@app.route('/updateStudent', methods=['PUT','POST','GET'])
def updateStudent():
 if 'role' in session:
  if session.get('role') == 'admin':
   if request.method=='GET':
    faculty = request.form.get('first_name')
    print(faculty)
    student_id=request.args.get('id')
    obejectInstance=ObjectId(student_id)
    student=mongo.db.student.find_one({'_id':obejectInstance})
    name=str(student['name'])
    name=name.split()
    return render_template('users.html',
                           username=session['username'],
                           id=student_id,
                           firstname=name[0],
                           lastname=name[1],
                           course=student['course']
                           )
   else:

       course = request.form.get('course')
       student_id=request.form.get('id')
       first_name = request.form.get('first_name')
       last_name = request.form.get('last_name')
       obejectInstance = ObjectId(student_id)
       course_desc=findFaculity(course)
       students=mongo.db.student.find_one({'_id': obejectInstance,'course':course_desc})
       student = mongo.db.student.find_one({'_id': obejectInstance,'course':course_desc})

       if student == None:
           count=mongo.db.student.find({'course':course_desc}).count()+1
           student = mongo.db.student.find_one({'_id': obejectInstance})
           mode=student['mode']
           date=str(student["year of reg"])
           date=date.split('-')
           month=date[1]
           year=date[0]
           year=year[2]+year[3]
           mode=find_mode(mode)
           regnum=course+"/"+mode+"/"+str(count)+"/"+month+"/"+(year)
           print(regnum)
           name=first_name+" "+last_name
           print(name)
           mongo.db.student.update({"_id": obejectInstance}, {"$set": {"reg": regnum,'name':name,'course':course_desc}})
           updatedStudent=mongo.db.student.find_one({"_id": obejectInstance})
           flash("You have successfully updated, " + name + " is registration number is " + updatedStudent['reg'])

           return render_template('users.html',
                                  username=session['username'],
                                  id=student_id,
                                  firstname=first_name,
                                  lastname=last_name,
                                  course=updatedStudent['course']
                                  )
       else:
           name = first_name + " " + last_name
           mongo.db.student.update({"_id": obejectInstance},{"$set": { 'name': name}})
           updatedStudent = mongo.db.student.find_one({"_id": obejectInstance})
           flash("You have successfully updated, " + name + " is registration number is " + updatedStudent['reg'])
           return render_template('users.html',
                                  username=session['username'],
                                  id=student_id,
                                  firstname=first_name,
                                  lastname=last_name,
                                  course=updatedStudent['course']
                                  )


       return {}
  else:
      return render_template('login.html')
 else:
     return render_template('login.html')


@app.route('/updateLecturer',methods=['PUT','POST','GET'])
def updateLecturer():
  if 'role' in session:
   if session.get('role') == 'admin':
    if request.method == 'GET':
        faculty = request.form.get('first_name')
        print(faculty)
        lecturer_id = request.args.get('id')
        obejectInstance = ObjectId(lecturer_id)
        lecturer = mongo.db.lecturers.find_one({'_id': obejectInstance})
        name = str(lecturer['name'])
        name = name.split()
        return render_template('lecturer.html',
                               username=session['username'],
                               id=lecturer_id,
                               firstname=name[0],
                               lastname=name[1],
                               course=lecturer['faculty'],
                               mode=lecturer['mode']
                               )
    else:
        faculty = request.form.get('course')
        lecturer_id = request.form.get('id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        mode=request.form.get('mode')
        teaching_mode=find_lec_mode(mode)

        obejectInstance = ObjectId(lecturer_id)
        faculty_desc = findFaculity(faculty)
        lecturer = mongo.db.lecturers.find_one({'_id': obejectInstance, 'faculty': faculty_desc,'mode':teaching_mode})


        if lecturer == None:
            lec = mongo.db.lecturers.find_one({'_id': obejectInstance})
            dep=lec['department']
            staff_number=str(lec['staff_num'])
            staff_number=staff_number.split('/')
            print(staff_number)
            staff_number[1]=mode
            print(staff_number)
            staff_num = staff_number[0] + "/" +staff_number[1] + "/" + staff_number[2] + "/" + staff_number[3] + "/" +staff_number[4]
            print(staff_num)
            name = first_name + " " + last_name
            print(name)
            mode=find_lec_mode(mode)
            print(mode)
            mongo.db.lecturers.update({"_id": obejectInstance},{"$set": {"staff_num": staff_num, 'name': name, 'faculty': faculty_desc,'mode':mode}})
            updated_lec=mongo.db.lecturers.find_one({"_id": obejectInstance})
            print(updated_lec)
            flash("You have successfully updated, " + name + " is staff number is " + updated_lec['staff_num'])
            return render_template('lecturer.html',
                                   username=session['username'],
                                   id=lecturer_id,
                                   firstname=first_name,
                                   lastname=last_name,
                                   course=updated_lec['faculty'],
                                   mode=updated_lec['mode']
                                   )
        else:
           name = first_name + " " + last_name
           mongo.db.lecturers.update({"_id": obejectInstance}, {"$set": {'name': name}})
           updated_lec = mongo.db.lecturers.find_one({"_id": obejectInstance})
           flash("You have successfully updated, " +name+ " is staff number is"+updated_lec['staff_num'])
           return render_template('lecturer.html',
                                  username=session['username'],
                                  id=lecturer_id,
                                  firstname=first_name,
                                  lastname=last_name,
                                  course=updated_lec['faculty'],
                                  mode=updated_lec['mode']
                                  )

        return {}
   else:
       return render_template('login.html')
  else:
    return render_template('login.html')

@app.route('/updateCourse',methods=['PUT','POST','GET'])
def updateCourse():
 if 'role' in session:
  if session.get('role') == 'admin':
    course_id=request.args.get('id')
    course_id=ObjectId(course_id)
    if request.method =='GET':
        course = mongo.db.course.find_one({'_id': course_id})
        type=course['type']
        year=course['year']
        semester=course['semester']
        description=course['description']
        return render_template('add-course.html',
                               username=session['username'],
                               id=course_id,
                               year=int(year),
                               semester=int(semester),
                               description=description
                               )
    else:
        year=request.form.get('year')
        semester=request.form.get('semester')
        unit_desc=request.form.get('unit_desc')
        course_id= request.form.get('id')
        course_id=ObjectId(course_id)
        course = mongo.db.course.find_one({'_id': course_id,'year':year,'semester':semester})
        if course==None:
          course = mongo.db.course.find_one({'_id': course_id})
          count = mongo.db.course.find( {'year': year, 'semester': semester,'type':course['type']}).count()
          type=course['type']
          print(type)
          code=str(year)+str(semester)+str(count)
          print(code)
          course_code=type+" "+ code
          print(course_code)
          mongo.db.course.update({"_id": course_id}, {"$set": {'description': unit_desc,'code':code,'course_code':course_code,'year':year,'semester':semester}})
          updated_unit = mongo.db.course.find_one({"_id": course_id})
          flash("You have successfully updated, " +updated_unit['description'] + " is unit code is" + updated_unit['course_code'])
          return render_template('add-course.html',
                                 username=session['username'],
                                 id=course_id,
                                 year=int(updated_unit['year']),
                                 semester=int(updated_unit['semester']),
                                 description=updated_unit['description']
                                 )


        else:
            year = request.form.get('year')
            semester = request.form.get('semester')
            unit_desc = request.form.get('unit_desc')
            course_id = request.form.get('id')
            course_id = ObjectId(course_id)
            mongo.db.course.update({"_id": course_id}, {
                "$set": {'description': unit_desc}})
            updated_unit = mongo.db.course.find_one({"_id": course_id})
            flash("You have successfully updated, " + updated_unit['description'] + " is unit code is" + updated_unit['course_code'])
            return render_template('add-course.html',
                                   username=session['username'],
                                   id=course_id,
                                   description=updated_unit['description']
                                   )




        return {}





    return {}
  else:
      return render_template('login.html')
 else:
     return render_template('login.html')



@app.route('/getStudents',methods=['POST','GET'])
def getStudents():
 if 'role' in session:
   if session.get('role') == 'admin':
    if request.method == 'GET':
     students=[]
     offset=0
     limit=5
     if request.args.get('faculty') == None:
      count = mongo.db.student.find({'active':True}).count()
      if count!=0:
       myCursor=mongo.db.student
       if request.args.get('offset'):
         offset=int(request.args['offset'])
         limit=int(request.args['limit'])
       next=offset+limit
       previous=offset-limit
       starting_id=myCursor.find({'active':True}).sort('_id',pymongo.ASCENDING)
       last_id=starting_id[offset]['_id']
       students_cursor=myCursor.find({'_id':{'$gte':last_id},'active':True}).sort('_id',pymongo.ASCENDING).limit(limit)
       for student in students_cursor:
         students.append(student)


       if(offset+1==offset +len(students)):
         items = 'Showing ' + str(offset + 1) + ' of ' + str(count) + ' Entries'
       else:
        items='Showing '+str(offset+1) +' to '+str(offset +len(students)) + ' of '+ str(count) +' Entries'


       return render_template('users.html',
                           username=session['username'],
                           students=students,
                           next=next,
                           previous=previous,
                           total=count,
                           entries=items
                           )
      else:
          flash("Oops! cannot find students,have you enroll any student?")
          return render_template('users.html',
                                 username=session['username']
                                 )

     else:
         faculty_code=request.args.get('faculty')
         department_code= request.args.get('department')
         course=findFaculity(faculty_code)
         print(course)
         count = mongo.db.student.find({'course':course,'active':True}).count()
         if count!=0:
          myCursor = mongo.db.student
          if request.args.get('offset'):
             offset = int(request.args['offset'])
             limit = int(request.args['limit'])
          next = offset + limit
          previous = offset - limit
          starting_id = myCursor.find({'course':course,'active':True}).sort('_id', pymongo.ASCENDING)
          print(starting_id)
          last_id = starting_id[offset]['_id']
          students_cursor = myCursor.find({'_id': {'$gte': last_id},'course':course,'active':True}).sort('_id', pymongo.ASCENDING).limit(limit)
          for student in students_cursor:
             print(student)
             students.append(student)

          if (offset + 1 == offset + len(students)):
             items = 'Showing ' + str(offset + 1) + ' of ' + str(count) + ' Entries'
          else:
             items = 'Showing ' + str(offset + 1) + ' to ' + str(offset + len(students)) + ' of ' + str(
                 count) + ' Entries'
          return render_template('users.html',
                                username=session['username'],
                                students=students,
                                next=next,
                                previous=previous,
                                total=count,
                                entries=items,
                                faculty=faculty_code,
                                department = department_code
                                )
         else:
             flash("Oops! cannot find students,have you enroll any student for that faculty?")
             return render_template('users.html',
                                    username=session['username']
                                    )
    else:
     return {}
   else:
       return render_template('login.html')
 else:
     return render_template('login.html')

@app.route('/getLecturers')
def getLecturers():
 if 'role' in session:
  if session.get('role') == 'admin':
    lecturers = []
    offset = 0
    limit = 5
    if request.args.get('faculty') == None:
     count = mongo.db.lecturers.find({'active':True}).count()
     if(count!=0):
      myCursor = mongo.db.lecturers
      if request.args.get('offset'):
        offset = int(request.args['offset'])
        limit = int(request.args['limit'])
      next = offset + limit
      previous = offset - limit
      starting_id = myCursor.find({'active':True}).sort('_id', pymongo.ASCENDING)
      last_id = starting_id[offset]['_id']
      lecturers_cursor = myCursor.find({'_id': {'$gte': last_id},'active':True}).sort('_id', pymongo.ASCENDING).limit(limit)
      for lecturer in lecturers_cursor:
         lecturers.append(lecturer)

      if (offset + 1 == offset + len(lecturers)):
         items = 'Showing ' + str(offset + 1) + ' of ' + str(count) + ' Entries'
      else:
        items = 'Showing ' + str(offset + 1) + ' to ' + str(offset + len(lecturers)) + ' of ' + str(count) + ' Entries'

      return render_template('lecturer.html',
                           username=session['username'],
                           lecturers=lecturers,
                           next=next,
                           previous=previous,
                           total=count,
                           entries=items
                           )
     else:
         flash("Oops! cannot find lecturers,have you added any lecturer?")
         return render_template('lecturer.html',
                                username=session['username']
                                )
    else:
        faculty_code=request.args.get('faculty')
        department_code = request.args.get('department')
        faculty_desc=findFaculity(faculty_code)
        count = mongo.db.lecturers.find({'faculty':faculty_desc}).count()
        if(count!=0):
         myCursor = mongo.db.lecturers
         if request.args.get('offset'):
            offset = int(request.args['offset'])
            limit = int(request.args['limit'])
         next = offset + limit
         previous = offset - limit
         starting_id = myCursor.find({'faculty':faculty_desc}).sort('_id', pymongo.ASCENDING)
         last_id = starting_id[offset]['_id']
         lecturers_cursor = myCursor.find({'_id': {'$gte': last_id},'faculty':faculty_desc}).sort('_id', pymongo.ASCENDING).limit(limit)
         for lecturer in lecturers_cursor:
             lecturers.append(lecturer)

         if (offset + 1 == offset + len(lecturers)):
             items = 'Showing ' + str(offset + 1) + ' of ' + str(count) + ' Entries'
         else:
            items = 'Showing ' + str(offset + 1) + ' to ' + str(offset + len(lecturers)) + ' of ' + str(
                count) + ' Entries'

         return render_template('lecturer.html',
                               username=session['username'],
                               lecturers=lecturers,
                               next=next,
                               previous=previous,
                               total=count,
                               entries=items,
                               department=department_code,
                               faculty=faculty_code
                               )
        else:
            flash("Oops! cannot find any lecturer from that faculty")
            return render_template('lecturer.html',
                                   username=session['username']
                                   )
  else:
      return render_template('login.html')
 else:
     return render_template('login.html')

@app.route('/deleteLecture')
def deleteLecture():
 if 'role' in session:
  if session.get('role') == 'admin':
    lecturer_id = request.args.get('id')
    obejectInstance = ObjectId(lecturer_id)
    if request.args.get('delete')==None:
     lecturer = mongo.db.lecturers.find_one({'_id': obejectInstance})
     print(lecturer)
     flash("Are you want to delete "+str(lecturer['name'] +" ?"))
     return render_template('delete-lecturer.html',
                           username=session['username'],
                           id=lecturer_id
                           )
    else:
        mongo.db.lecturers.update({"_id": obejectInstance}, {
            "$set": {'active':False}})

        return redirect(url_for('getLecturers'))
  else:
      return render_template('login.html')
 else:
     return render_template('login.html')
@app.route('/deleteStudent')
def deleteStudent():
 if 'role' in session:
  if session.get('role') == 'admin':
    student_id = request.args.get('id')
    obejectInstance = ObjectId(student_id)
    if request.args.get('delete')==None:
     student = mongo.db.student.find_one({'_id': obejectInstance})
     flash("Are you want to delete "+str(student['name']+ " ?"))
     return render_template('delete-student.html',
                           username=session['username'],
                           id=student_id
                           )
    else:
        mongo.db.student.update({"_id": obejectInstance}, {
            "$set": {'active': False}})
        return redirect(url_for('getStudents'))
  else:
      return render_template('login.html')
 else:
     return render_template('login.html')

@app.route('/deleteCourse')
def deleteCourse():
 if 'role' in session:
   if session.get('role') == 'admin':
    course_id = request.args.get('id')
    obejectInstance = ObjectId(course_id)
    if request.args.get('delete') == None:
        course = mongo.db.course.find_one({'_id': obejectInstance})
        flash("Are you want to delete " + str(course['course_code'] +" "+ str(course['description'])+" ?"))
        return render_template('delete-course.html',
                           username=session['username'],
                           id=course_id
                           )
    else:
        mongo.db.course.update({"_id": obejectInstance}, {
            "$set": {'active': False}})
        return redirect(url_for('getCourse'))
   else:
       return render_template('login.html')
 else:
     return render_template('login.html')


@app.route('/settings',methods=['POST','GET'])
def settings():
    if session.get('role'):
        if session.get('role') == 'admin':
           if request.method == 'GET':
             return render_template('settings.html',username=session['username'])
           else:
             old_password=request.form.get("old_password")
             password=request.form.get("password")
             password_confirm=request.form.get("password_confirm")
             if password == password_confirm:
               username=session['username']
               admin = mongo.db.admin.find_one({'name': username})
               if admin:
                   if bcrypt.hashpw(old_password.encode('utf-8'), admin['password']) == admin['password']:
                       hashpass = bcrypt.hashpw(request.form.get("password").encode('utf-8'), bcrypt.gensalt())
                       user_id=ObjectId(admin['_id'])
                       mongo.db.admin.update({"_id": user_id}, {
                           "$set": {'password': hashpass}})
                       flash("You have successfully updated your password")
                       return render_template('settings.html', username=session['username'],flag=True)
                   else:
                       flash( "Invalid Password")
                       return render_template('settings.html', username=session['username'],flag=False)
               else:
                   flash( "Invalid Password")
                   return render_template('settings.html', username=session['username'],flag=False)
             else:
                 flash("Password does not match")
                 return render_template('settings.html', username=session['username'], flag=False)
        else:
            return render_template('lecturer-login.html')
    else:
        return render_template('lecturer-login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['pass']
        admin = mongo.db.admin.find_one({'name': username})
        if admin:
            if bcrypt.hashpw(password.encode('utf-8'), admin['password']) == admin['password']:
                session['role']='admin'
                session['username']=username
                return redirect(url_for('index'))
            else:
                error="Invalid Username and Password"
        else:
            error = "Invalid Username and Password"
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    session.clear()
    return  redirect(url_for('login'))
@app.route('/lecturer_logout')
def lecturer_logout():
    session.clear()
    return  redirect(url_for('lecturerLogin'))

#student routes


@app.route('/registerUnit',methods=['POST','GET'])
def registerUnit():
        year=request.args.get('year')
        semester=request.args.get('semester')
        id=request.args.get('id')
        id=ObjectId(id)
        if year!=None:
            courseList=[]
            student = mongo.db.student.find_one({'_id': id})
            myCursor = mongo.db.course
            course_cursor = myCursor.find({ 'faculty': str(student['course']), 'year': year,'semester': semester, 'active': True}).sort('_id', pymongo.ASCENDING)
            for course in course_cursor:
                courseList.append(course)
            print(courseList)
            return render_template('register-unit.html',courses=courseList,username=session['username'],id=id)
        else:
         flag=False
         error="You have already registered"
         student_id=request.args.get('id')
         student_id = ObjectId(student_id)
         print(id)
         username=request.args.get('username')
         units_ids=request.args.getlist('checkbox')
         student = mongo.db.student.find_one({'_id': student_id})
         for unit_id in units_ids:
             unit_id = ObjectId(unit_id)
             unit = mongo.db.course.find_one({'_id': unit_id})
             registered = mongo.db.registered_units.find_one({"student_id": student['_id'], 'unit_id':unit_id })
             if registered:
                 flag=True
                 error=error+"\n"+unit['course_code']
                 print(error)
             else:
                 mongo.db.registered_units.insert({"student_id": student['_id'], 'unit_id': unit_id})
         if flag:
             flash(error)
         return render_template('register-unit.html',username=session['username'],id=id)
@app.route('/addUnitToTeach')
def addUnitToTeach():
  if session.get('role'):
     if session.get('role') == 'lecturer':

        year=request.args.get('year')
        semester=request.args.get('semester')
        id=request.args.get('id')
        id=ObjectId(id)
        if year!=None:
            courseList=[]
            lecture = mongo.db.lecturers.find_one({'_id': id})
            myCursor = mongo.db.course
            course_cursor = myCursor.find({ 'faculty': str(lecture['faculty']), 'year': year,'semester': semester, 'active': True}).sort('_id', pymongo.ASCENDING)
            for course in course_cursor:
                courseList.append(course)
            print(courseList)
            return render_template('add-unit-to-teach.html',courses=courseList,username=session['username'],id=id,year=int(year),semester=int(semester))
        else:
         flag=False
         error="You have already add"
         lecturer_id = ObjectId(id)
         print(id)

         units_ids=request.args.getlist('checkbox')
         lecturer = mongo.db.lecturers.find_one({'_id':lecturer_id})
         for unit_id in units_ids:
             unit_id = ObjectId(unit_id)
             unit = mongo.db.course.find_one({'_id': unit_id})
             registered = mongo.db.unit_to_teach.find_one({"lecturer_id": lecturer['_id'], 'unit_id':unit_id })
             if registered:
                 flag=True
                 error=error+"\n"+unit['course_code']
                 print(error)
             else:
                 mongo.db.unit_to_teach.insert({"lecturer_id": lecturer['_id'], 'unit_id': unit_id})
         if flag:
             flash(error)
         return render_template('add-unit-to-teach.html',username=session['username'],id=id)
     else:
        return render_template('lectuer-login')
  else:
     return render_template('lecturer-login.html')

@app.route('/getRegisteredUnit',methods=['POST','GET'])
def getRegisteredUnit():
    if 'role' in session:
        id = request.args.get('id')
        flag=request.args.get('flag')
        id = ObjectId(id)
        role = session.get('role')
        if role == 'student':
          courses = []
          units = mongo.db.registered_units.find({'student_id': id})
          for unit in units:
           course = mongo.db.course.find_one({'_id': unit['unit_id']})
           courses.append(course)
          return render_template('registered-unit.html', id=id,courses=courses,username=session['username'])
        elif role =='lecturer':
            courses = []
            units = mongo.db.unit_to_teach .find({'lecturer_id': id})
            for unit in units:
                course = mongo.db.course.find_one({'_id': unit['unit_id']})
                courses.append(course)
                print(course)
            return render_template('view-registered-unit.html', id=id, courses=courses, username=session['username'],flag=flag)


@app.route('/dropCourse',methods=['POST','GET'])
def dropCourse():
    course_id=ObjectId(request.args.get('course_id'))
    student_id=ObjectId(request.args.get('student_id'))
    unit = mongo.db.registered_units.remove({'student_id': student_id,'unit_id':course_id})

    print(unit)
    return redirect(url_for('getRegisteredUnit',id=student_id))


def allowed_file(filename):
    return '.'in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/updateProfile', methods=['POST','GET'])
def updateProfile():
    id = request.args.get('id')
    if request.method =='GET':
        return render_template('student-updateProfile.html',username=session['username'],id=id)
    else:
     if 'file' not in request.files:
         flash('no file part')
         return render_template('student-updateProfile.html',username="", id=id)
     file=request.files['file']
     if file.filename=='':
         flash("no Image selected for uploading")
         return render_template('student-updateProfile.html',username="", id=id)
     if file and allowed_file(file.filename):
         id=ObjectId(id)
         student = mongo.db.student.find_one({'_id': id})
         stringStudent=student['reg']
         s1="".join(c for c in stringStudent if c.isalnum())
         print(s1)
         if (mongo.db.fs.files.find()):
           users=mongo.db.fs.files.find()
           for user in users:
            print(user)

         print("file found")

         img_id=grid_fs.put(file,content_type=file.content_type,filname=s1)
         print(student)
         mongo.db.student.update({"_id":student['_id']},{"$set":{ "profile_url":img_id}})
         student_updated = mongo.db.student.find_one({'_id': id})
         image_url=student_updated['profile_url']
        #image_file=mongo.send_file(image_url)
         image_file=grid_fs.get(image_url)
         base_64_data=codecs.encode(image_file.read(),'base64')
         decodeit=open('hello_leve.jpg','wb')
         decodeit.write(base64.b64decode(base_64_data))
         decodeit.close()
         img=base_64_data.decode('utf-8')
         print(img)
         #print(url_for('127.0.0.1:5000/file',image_file))

         #return render_template('student-updateProfile.html', username=session['username'], id=id,img=img,status=True)
         return url_for('127.0.0.1:5000/file {{image_file}}')
        # return f'''
        # <img src="data:image/png;base64/{{img}}" alt="myImage">
        #  '''
     else:
         flash("Please select a valid image file, allowed image are - png, jpg, jpeg, gif .")
         return render_template('student-updateProfile.html', username=session['username'], id=id)


@app.route('/file/<filename>')
def file(filename):
    return mongo.send_file(filename)

@app.route('/getProfile',methods=['GET'])
def getupdate():
    data = request.get_json()
    reg = data['reg']
    student = mongo.db.student.find_one({'reg': reg})
    print(student);
    image_url = student['profile_url']
    s1 = "".join(c for c in student['reg'] if c.isalnum())
    print(s1)
    # image_file=mongo.send_file(image_url)
    image_file = grid_fs.get(image_url)
    imgs=mongo.db.fs.files.find()
    for img in imgs:
        print(img)
    base_64_data = codecs.encode(image_file.read(), 'base64')
    decodeit = open('image/'+s1+'.jpg', 'wb')
    decodeit.write(base64.b64decode(base_64_data))
    decodeit.close()
    img = base_64_data.decode('utf-8')
    print(img)

    return {}

#lecturer route
@app.route('/getStudentByUnit')
def getStudentByUnit():
 if session.get('role'):
   if session.get('role') == 'lecturer':
    students=[]
    course_id=request.args.get('course_id')
    id=request.args.get('id')
    id=ObjectId(id)
    course_id=ObjectId(course_id)
    current_unit=mongo.db.course.find_one({'_id':course_id})
    course_code=str(current_unit['course_code']).lower()
    print(current_unit)
    units=mongo.db.registered_units.find({'unit_id':course_id})
    for unit in units:
        student=mongo.db.student.find_one({'_id':unit['student_id']},{'_id':False,'password':False,'profile_url':False})
        students.append(student)
    if len(students) == 0:
        courses = []
        units = mongo.db.unit_to_teach.find({'lecturer_id': id})
        for unit in units:
            course = mongo.db.course.find_one({'_id': unit['unit_id']})
            courses.append(course)
        flag=True
        flash('This unit has not yet been registered')
        return render_template('student-list.html',flag=flag,id=id,username=session['username'])
    else:
        return render_template('student-list.html',students=students,id=id,username=session['username'],unit_code=course_code)
   else:
      return render_template('lecturer-login.html')
 else:
     return render_template('lecturer-login.html')


@app.route('/getRegisteredUnits')
def getRegisteredUnits():
    courses=[]
    reg=request.args.get('reg')
    student=mongo.db.student.find_one({'reg':reg})
    if student is not None:
        student_id=student['_id']
        units=mongo.db.registered_units.find({'student_id':student_id})
        for unit in units:
            course=mongo.db.course.find_one({'_id':unit['unit_id']},{'_id':False})
            courses.append(course)
    return {'message':courses}


@app.route('/takeAttendance',methods=['GET','POST'])
def takeAttendance():
 if session.get('role'):
   if session.get('role') == 'lecturer':
    id = request.args.get('id')
    id = ObjectId(id)
    course_id=ObjectId(request.args.get('course_id'))
    print(course_id)
    courses = []
    units = mongo.db.unit_to_teach.find({'lecturer_id': id})
    for unit in units:
        course = mongo.db.course.find_one({'_id': unit['unit_id']})
        courses.append(course)
        print(course)
    return render_template('take-attendance.html', id=id, courses=courses, username=session['username'] )
   else:
    return render_template('lecturer-login.html')
 else:
   return render_template('leccturer-login.html')


def markAttendances(reg,course_id):
    todayDate=str(date.today())
    students=mongo.db.student.find()
    for student in students:
        reg_number=str(student['reg']).split('/')
        reg_number=reg_number[0]+reg_number[1]+reg_number[2]+reg_number[3]+reg_number[4]
        if reg_number==reg:
            current_id=student['_id']
            result= mongo.db.attendances_date.find_one({'date':todayDate})
            if result==None:
              attendance_date = {'date': todayDate}
              mongo.db.attendances_date.insert(attendance_date)
            date_id=mongo.db.attendances_date.find_one({'date':todayDate})
            date_id=date_id['_id']
            print(date_id)
            print('course id')
            print(course_id)
            marked=mongo.db.mark_attendances.find_one({'date_id':date_id,'student_id':current_id,'course_id':course_id})
            if marked==None:
                data={'date_id':date_id,'student_id':current_id,'course_id':course_id}
                mongo.db.mark_attendances.insert_one(data)
                present_result = mongo.db.present.find_one({'unit_id':course_id,'student_id':current_id})
                if present_result==None:
                    present_data={'unit_id':course_id,'student_id':current_id,'present_num':1}
                    mongo.db.present.insert_one(present_data)
                else:
                    present = mongo.db.present.find_one({'unit_id': course_id, 'student_id': current_id})
                    present_number = present['present_num']
                    present_number = int(present_number) + 1
                    mongo.db.present.update_one(
                        {'_id': present['_id']},
                        {"$set": {'present_num': present_number}}

                    )
    return{}




@app.route('/takeUnitAttendance',methods=['GET'])
def takeUnitAttendance():
  if session.get('role'):
    if session.get('role') == 'lecturer':
        id = request.args.get('id')
        course_id = ObjectId(request.args.get('course_id'))
        print(course_id)
        start = request.args.get('start')
        if start:
            if start == "True":
                status = True
            students = []
            lec_num=mongo.db.units_num_classes.find_one({'unit_id':course_id})
            if lec_num==None:
                dates = {'unit_id': course_id, 'lectures_num': 1}
                mongo.db.units_num_classes.insert(dates)
            else:
                lecture_num=int(lec_num['lectures_num'])+1
                mongo.db.units_num_classes.update_one(
                        {'_id':lec_num['_id']},
                        {'$set':{'lectures_num':lecture_num}}
                    )
            units = mongo.db.registered_units.find({'unit_id': course_id})
            for unit in units:
                print(unit)
                student = mongo.db.student.find_one({'_id': unit['student_id']})
                print(student)
                image_url = student['profile_url']
                print(image_url)
                s1 = "".join(c for c in student['reg'] if c.isalnum())
                print(s1)
                image_file = grid_fs.get(image_url)
                imgs = mongo.db.fs.files.find()
                base_64_data = codecs.encode(image_file.read(), 'base64')
                decodeit = open('image/' + s1 + '.jpg', 'wb')
                decodeit.write(base64.b64decode(base_64_data))
                decodeit.close()
                img = base_64_data.decode('utf-8')
                students.append(student)
            if len(students) == 0:
                return {'data': 'This unit has not been registered'}
            path = 'image'
            images = []
            classNames = []
            myList = os.listdir(path)
            print(myList)
            for cls in myList:
                curImg = cv2.imread(f'{path}/{cls}')
                # print(curImg)
                images.append(curImg)
                classNames.append(os.path.splitext(cls)[0])
            print(classNames)
            encodingListKnow = findEncodings(images)
            print("Encoding completed")
            cap = cv2.VideoCapture(0)  # reading image from webcam
            while status:
                sucess, img = cap.read()  # resizing image
                imgs = cv2.resize(img, (0, 0), None, 0.25, 0.25)
                imgs = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                faceCurFrame = face_recognition.face_locations(imgs)
                encodeCurFrame = face_recognition.face_encodings(imgs, faceCurFrame)
                for encodeFace, faceloc in zip(encodeCurFrame, faceCurFrame):
                    matches = face_recognition.compare_faces(encodingListKnow, encodeFace)
                    facedis = face_recognition.face_distance(encodingListKnow, encodeFace)
                    print(facedis)
                    print('show')
                    matchIndex = np.argmin(facedis)
                    if matches[matchIndex]:
                        reg = classNames[matchIndex].upper()
                        print(reg)
                        y1, x2, y2, x1 = faceloc
                        # y1,x2,y2,x1 =y1*4,x2*4,y2*4,x1*4
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0))
                        cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, reg, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                        markAttendances(reg, course_id)
                cv2.imshow('class Attendance', img)
                print("showing")
                if cv2.waitKey(1) == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()
            flash("You have completed taking attendances")
            return redirect(url_for('takeAttendance',id=id))



        if course_id:
            print(course_id)
            print("course id")
            return render_template('take-attendance.html', id=id, username="man", course_id=course_id)
        courses = []
        units = mongo.db.unit_to_teach.find({'lecturer_id': id})
        for unit in units:
            course = mongo.db.course.find_one({'_id': unit['unit_id']})
            courses.append(course)
            print(course)
        return render_template('take-attendance.html', id=id, courses=courses, username="man", )
    else:
       return render_template('lecturer-login')
  else:
    return render_template('lecturer-login,html')
@app.route('/viewAttendance',methods=['GET'])
def viewAttendance():
 if session.get('role'):
   if session.get('role') == 'lecturer':
    id=request.args.get('id')
    course_id=request.args.get('course_id')
    error=request.args.get('error')
    id=ObjectId(id)
    dates=[]
    students=[]
    courses=[]

    if course_id == None:
     course_cursor=mongo.db.unit_to_teach.find({"lecturer_id":id})
     for course in course_cursor:
        courses.append(mongo.db.course.find_one({'_id':course['unit_id']}))
     return render_template('view-attendance.html', courses=courses,username=session['username'],id=id)
    else:
        course_id=ObjectId(course_id)
        lectures = mongo.db.units_num_classes.find_one({'unit_id':course_id})
        print(lectures)
        if lectures!=None:
         num_lec=lectures['lectures_num']
        else:
          course_cursor = mongo.db.unit_to_teach.find({"lecturer_id": id})
          for course in course_cursor:
             courses.append(mongo.db.course.find_one({'_id': course['unit_id']}))
          flash("Attendances for this unit has not yet be taken")
          return render_template('view-attendance.html', courses=courses,username=session['username'],id=id)
        marked_unit_cursor=mongo.db.present.find({'unit_id':course_id})

        for marked_unit in marked_unit_cursor:
            student=mongo.db.student.find_one({'_id':marked_unit['student_id']})
            present =int(marked_unit['present_num'])
            total=int(num_lec)
            percentage=(present/total)*100
            percentage=str(percentage)+"%"
            student_update={'name':student['name'],'reg':student['reg'],'day_present':marked_unit['present_num'],'total_lectures':num_lec,'percentage':percentage}
            students.append(student_update)
        if len(students)== 0:
            course_cursor = mongo.db.unit_to_teach.find({"lecturer_id": id})
            for course in course_cursor:
                courses.append(mongo.db.course.find_one({'_id': course['unit_id']}))
            flash("Attendances for this unit has not yet be taken")
            return render_template('view-attendance.html', courses=courses, username=session['username'], id=id)
        else:
         return render_template('view-attendance.html',username=session['username'], id=id, students=students)
   else:
       return render_template('lecturer-login,html')
 else:
     return render_template('lecturer-login,html')





@app.route('/',methods=['GET', 'POST'])
def index():
    if 'role' in session:
      if session.get('role')=='admin':
         username=session['username']
         return render_template('index.html',username=session['username'])
    return render_template('login.html')
@app.route('/home')
def home():
  return  index()

@app.route('/dashBoard')
def dashBoard():
    if 'role' in session:
        role=session.get('role')
        if role== 'student':
            name=request.args.get('name')
            id=request.args.get('id')

            return render_template('student-dash-board.html',username=session['username'],id=id)
        else:
            return render_template('student-login.html')

    return render_template('student-login.html')
@app.route('/lecturerDashBoard')
def lecturerDashboard():
    if session.get('role'):
         if session.get('role') =='lecturer':
          id=request.args.get('id')
          return render_template('lecturer-dashboard.html',id=id,username=session.get('username'))
         else:
             return render_template('lecturer-login.html')
    else:
        return render_template('lecturer-login.html')
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        admin = mongo.db.admin
        existing_user = admin.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            admin.insert({'name': request.form['username'], 'password': hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))

        return 'That username already exists!'

    return render_template('register.html')
@app.route('/registerStudent',methods=['GET','POST'])
def registerStudent():
    if 'username' in session:
        return render_template('user-edit.html', username=session['username'])
    return render_template('login.html')



@app.route('/registerLecturer',methods=['GET','POST'])
def registerLecturer():
    if 'username' in session:
        return render_template('lecturer-edit.html', username=session['username'])
    return render_template('login.html')




def findEncodings(images): #Function that Finds encoding on face
    encodingList=[]
    for img in images:
        img=cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
        encode=face_recognition.face_encodings(img)[0]
        encodingList.append(encode)
    return encodingList

@app.route('/studentLogin',methods=['POST','GET'])
def studentLogin():
    if request.method=='GET':
       return render_template('student-login.html')
    else:
        reg_number=request.form.get('reg_number')
        reg_number=str(reg_number)
        reg_number=reg_number.upper()
        print(reg_number)
        password=request.form.get('pass')
        student = mongo.db.student.find_one({'reg': reg_number})
        if student:
            if bcrypt.hashpw(password.encode('utf-8'), student['password']) == student['password']:
                session.clear()
                session['role'] = 'student'
                name = student['name']
                name = str(name)
                name = name.split()
                name = name[0]
                session['username']=name

                return redirect(url_for('dashBoard',id=student['_id']))
    return render_template('student-login.html')

@app.route('/lecturerLogin',methods=['POST','GET'])
def lecturerLogin():
    if request.method=='GET':
     return render_template('lecturer-login.html')
    else:
        staff_number = request.form.get('reg_number')
        staff_number = str(staff_number )
        staff_number = staff_number .upper()
        print(staff_number )
        password = request.form.get('pass')
        lecturer = mongo.db.lecturers.find_one({'staff_num': staff_number })
        if lecturer:
            if bcrypt.hashpw(password.encode('utf-8'), lecturer['password']) == lecturer['password']:
                session.clear()
                session['role'] = 'lecturer'
                name = lecturer['name']
                name = str(name)
                name = name.split()
                name = name[0]
                session['username'] = name
                return redirect(url_for('lecturerDashboard', id=lecturer['_id']))
    return render_template('lecturer-login.html')









def findFaculity(faculty_code):
    if (faculty_code == "CS"):
        return "Computer Science"
    elif (faculty_code == "IT"):
        return "Information Technology"
    elif(faculty_code=="INTEL"):
        return "Telecommunication"
def findMode(student_mode):
    if student_mode=="M":
        return 'Self Sponsored'
    else:
        return 'Government Sponsored'
def find_mode(mode):
    if mode=="Government Sponsored":
        return "MG"
    else:
        return "M"
def find_lec_mode(mode):
    if (mode == "P"):
        return 'permanent'
    else:
        return 'part time'
def find_lec_mode_reverse(mode):
    if (mode == "permanent"):
        return 'P'
    else:
        return 'PT'

def find_school_code(school):
    if (school == 'School of Science Engineering and Technology'):
        return 'ENGT'
def find_school_code_desc(school_code):
    if (school_code == 'ENGT'):
        return 'School of Science Engineering and Technology'


if __name__== '__main__':
    app.secret_key = 'mysecret'
    app.run(port=5000,debug=True)



