from flask import Flask, redirect, url_for, render_template, request, session
import json
import random

app = Flask(__name__)
app.secret_key = "NgoCongHuan"

######################################## Controller 1 ########################################
@app.route("/", methods=["POST", "GET"])
def process1():
    if request.method == "POST":
        
        session['Employees'] = int(request.form['Employees'])
        session['Shifts'] = int(request.form['Shifts'])
        session['Days'] = int(request.form['Days'])
        session['EmployeePerShift'] = int(request.form['EmployeePerShift'])

        if ('Employees' in session and 'Shifts' in session and 'Days' in session):
            return redirect(url_for ("process2"))
        
    return render_template('process1.html')

######################################## Controller 2 ########################################
@app.route("/process2", methods=["POST", "GET"])
def process2():
  
  if ('Employees' in session and 'Shifts' in session and 'Days' in session):
    Employees = session['Employees']
    Shifts = session['Shifts']
    Days = session['Days']

  return render_template('process2.html', Employees=Employees, Shifts=Shifts, Days=Days)

######################################## Controller 3 ########################################
@app.route("/process3/<path:employees_shifts_temp>/<path:mapping_employees>", methods=["POST", "GET"])
def process3(employees_shifts_temp, mapping_employees):
    
    if ('Days' in session and 'EmployeePerShift' in session):
      days = session['Days']
      employee_per_shift = session['EmployeePerShift']
      employees = session['Employees']
      shifts = session['Shifts']
    
    average_shifts = average_shifts_per_employee(days, shifts, employee_per_shift, employees)

    # Load và chuyển đổi dữ liệu lấy từ client về
    employees_shifts_temp = json.loads(employees_shifts_temp)
    mapping_employees = json.loads(mapping_employees)

    # Áp dụng hàm create_employees_shifts
    employees_shifts, result_count_availbility = create_employees_shifts(employees_shifts_temp, mapping_employees, average_shifts)

    # Áp dụng hàm create_employee_availability
    employee_availability = create_employee_availability(employees_shifts, days)
    print("result_count_availbility: ", result_count_availbility)
    print("average_shifts: ", average_shifts)
    if result_count_availbility == True:
      bool = False
      n = 0
      while bool == False and n<100000:
        # Tạo lịch làm việc cho nhân viên
        count_shift_of_week, schedule_of_store = create_schedule(employee_availability, mapping_employees, employee_per_shift)
        bool = fitness_function(count_shift_of_week, average_shifts)
        print("bool: ", bool)
        n += 1
      print(n, bool)
    else:
      count_shift_of_week, schedule_of_store = create_schedule(employee_availability, mapping_employees, employee_per_shift)

    session['count_shift_of_week'] = count_shift_of_week 
    session['schedule_of_store'] = schedule_of_store

    # Redirect tới route /schedule bằng phương thức POST và truyền dữ liệu thông qua form data
    return redirect(url_for('schedule'))

# Hàm tạo lại một từ điển mới từ employees_shifts_temp , mapping_employees và tính tổng số ca mà nhân viên có thể làm trong tuần
def create_employees_shifts(employees_shifts_temp, mapping_employees, average_shifts):
  employees_shifts = {}
  for employeeID_temp, shift_temp in employees_shifts_temp.items():
    for employeeName, employeeID in mapping_employees.items():
        if str(employeeID) == employeeID_temp:
            employees_shifts[employeeName] = shift_temp
  count_availbility = {}
  for employeeName, days in employees_shifts.items():
    for day in days:
      for shift in day:
        if shift == 1:
          if employeeName in count_availbility.keys():
            count_availbility[employeeName] += 1
          else:
            count_availbility[employeeName] = 1
  bool = True
  for shift in count_availbility.values():
    if shift < average_shifts:
      bool = False
      return employees_shifts, bool
  return employees_shifts, bool

# Hàm khởi tạo từ điển chứa thông tin các ca nhân viên có thể làm trong ngày
def create_employee_availability(employees_shifts, days):
    employee_availability = {}
    for day in range(days):
      employee_availability['Ngày ' + str(day+1)] = []
    for day in range(days):
      shifts_in_day = []
      for shifts in employees_shifts.values():
        shifts_in_day.append(shifts[day])
      shift_by_employees = []
      shift_temp = []
      for j in range(len(shifts_in_day[0])):
        for i in range(len(shifts_in_day)):
          shift_temp.append(shifts_in_day[i][j])
        shift_by_employees.append(shift_temp)
        shift_temp = []
      employee_availability['Ngày ' + str(day+1)] = shift_by_employees
    return employee_availability

# Hàm tính số ca làm trung bình
def average_shifts_per_employee(days, shifts, employee_per_shift, employees):
  average_shifts = (days * shifts * employee_per_shift) // employees
  return average_shifts

# Hàm thích nghi dùng làm điều kiện dừng cho vòng lặp
def fitness_function(count_shift_of_week, average_shifts):
  bool = True
  for shift in count_shift_of_week.values():
    if shift < average_shifts:
      bool = False
      return bool
  return bool


# Thuật toán vét cạn để sắp xếp lịch cho nhân viên
def create_schedule(employee_availability, mapping_employees, employees_per_shift):
  # Khởi tạo lịch làm việc
  schedule_of_store = {}
  for day in employee_availability.keys():
    schedule_of_store[day] = []
  # Vòng lặp tạo lịch làm việc ngẫu nhiên
  for day in employee_availability.keys():
    # Tạo biến tạm chứa các ca làm việc
    shift_temp = {}
    for shift in range(len(employee_availability[day])):
      shift_temp[shift + 1] = []
    # Vòng lặp tìm kiếm những nhân viên có thể làm việc vào các ca trong ngày hiện tại đang duyệt
    for shift, schedule in enumerate(employee_availability[day]):
      for employee, binary in enumerate(schedule):
        if binary == 1:
          shift_temp[shift+1].append(employee+1)
    # Vòng lặp duyệt qua các nhân viên của mỗi ca
    for employees in shift_temp.values():
      # Nếu không có nhân viên nào làm được
      if len(employees) == 0:
        error = ['Không có nhân viên rảnh']
        schedule_of_store[day].append(error)
      # Nếu số lượng nhân viên không đủ chỉ tiêu
      elif (len(employees) > 0 and len(employees) < employees_per_shift):
        arr_employee = []
        employee_encryption = random.choice(employees)
        for name, encryption in mapping_employees.items():
            if int(employee_encryption) == int(encryption):
              employee_name = name
        arr_employee.append(employee_name)
        schedule_of_store[day].append(arr_employee)
      # Nếu số lượng nhân viên đủ chỉ tiêu
      else:
        arr_employee = []
        for _ in range(employees_per_shift):
          employee_encryption = random.choice(employees)
          employees.remove(employee_encryption)
          for name, encryption in mapping_employees.items():
            if int(employee_encryption) == int(encryption):
              employee_name = name
          arr_employee.append(employee_name)
        schedule_of_store[day].append(arr_employee)

  # Đếm số lượng số ca làm của mỗi nhân viên trong 1 tuần
  count_shift_of_week = {}
  for sc in schedule_of_store.values():
    for shift in sc:
      for employee in shift:
        if employee in count_shift_of_week.keys():
          count_shift_of_week[employee] += 1
        else:
          count_shift_of_week[employee] = 1
  return count_shift_of_week, schedule_of_store


######################################## Controller 4 ########################################
@app.route('/schedule')
def schedule():
  count_shift_of_week = session['count_shift_of_week']
  schedule_of_store = session['schedule_of_store']
  shifts = session['Shifts']
  return render_template('schedule.html', count_shift_of_week=count_shift_of_week, schedule_of_store=schedule_of_store, shifts=shifts)

if __name__ == '__main__':
    app.run(debug=True)
