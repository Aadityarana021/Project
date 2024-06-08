import mysql.connector


import mysql.connector

mydb = mysql.connector.connect(
  host="127.0.0.2",
  user="root",
  password="",
  database="mydatabase"
)

cursor = mydb.cursor()

# Define your SQL query
sql = "INSERT INTO users (name,email,password) VALUES (%s, %s, %s)"

# Define the data to insert into the table
data = ("value1", "value2", "value3")

# Execute the SQL query
cursor.execute(sql, data)

# Commit changes to the database
mydb.commit()

# Close the cursor and database connection
cursor.close()
mydb.close()

print(mydb)