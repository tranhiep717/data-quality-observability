
import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3399,
        user="root",
        password="",
        connection_timeout=3
    )

    print("Đã kết nối.")
    conn.close()

except mysql.connector.Error:
    print("PASS: Không thể kết nối MySQL.")
    print("Hệ thống đã bắt được lỗi kết nối.")
