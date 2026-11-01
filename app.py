from flask import Flask, request, jsonify, send_from_directory, session

import mysql.connector

from mysql.connector import Error

from werkzeug.security import generate_password_hash, check_password_hash



import os

import re

import ast

import subprocess

import sys

import tempfile



# =========================================================

# FLASK CONFIGURATION

# =========================================================



app = Flask(__name__)



app.secret_key = "neuroPrompt_secret_key_2026"



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")





# =========================================================

# MYSQL CONFIGURATION

# =========================================================



DB_CONFIG = {

    "host": "localhost",

    "user": "root",

    "password": "",

    "database": "neuroprompt_db"

}





# =========================================================

# DATABASE CONNECTION

# =========================================================



def get_db_connection():



    try:



        connection = mysql.connector.connect(

            host=DB_CONFIG["host"],

            user=DB_CONFIG["user"],

            password=DB_CONFIG["password"],

            database=DB_CONFIG["database"]

        )



        return connection



    except Error as e:



        print("Database connection error:", e)



        return None

def get_error_knowledge(language, error_type):

    connection = get_db_connection()

    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT cause, solution, example_code, fixed_code
            FROM error_knowledge
            WHERE language = %s
            AND error_type = %s
            LIMIT 1
        """, (language, error_type))

        return cursor.fetchone()

    except Error as e:
        print("Error knowledge lookup error:", e)
        return None

    finally:
        cursor.close()
        connection.close()

# =========================================================

# CREATE DATABASE AND TABLES

# =========================================================



def initialize_database():



    try:



        # First connect without selecting database

        connection = mysql.connector.connect(

            host=DB_CONFIG["host"],

            user=DB_CONFIG["user"],

            password=DB_CONFIG["password"]

        )



        cursor = connection.cursor()



        cursor.execute(

            "CREATE DATABASE IF NOT EXISTS neuroprompt_db"

        )



        cursor.close()

        connection.close()





        # Connect to actual database

        connection = mysql.connector.connect(

            host=DB_CONFIG["host"],

            user=DB_CONFIG["user"],

            password=DB_CONFIG["password"],

            database=DB_CONFIG["database"]

        )



        cursor = connection.cursor()





        # -------------------------------------------------

        # USERS TABLE

        # -------------------------------------------------



        cursor.execute("""

            CREATE TABLE IF NOT EXISTS users (

                id INT AUTO_INCREMENT PRIMARY KEY,

                username VARCHAR(100) NOT NULL UNIQUE,

                password VARCHAR(255) NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )

        """)





        # -------------------------------------------------

        # PROMPT TEMPLATES TABLE

        # -------------------------------------------------



        cursor.execute("""

            CREATE TABLE IF NOT EXISTS prompt_templates (

                id INT AUTO_INCREMENT PRIMARY KEY,

                user_id INT NOT NULL,

                title VARCHAR(200) NOT NULL,

                language VARCHAR(50) NOT NULL,

                body TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)

                    REFERENCES users(id)

                    ON DELETE CASCADE

            )

        """)





        # -------------------------------------------------

        # ANALYSIS HISTORY TABLE

        # -------------------------------------------------



        cursor.execute("""

            CREATE TABLE IF NOT EXISTS analysis_history (

                id INT AUTO_INCREMENT PRIMARY KEY,

                user_id INT NOT NULL,

                language VARCHAR(50) NOT NULL,

                code_input TEXT NOT NULL,

                detected_error TEXT NOT NULL,

                solution TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)

                    REFERENCES users(id)

                    ON DELETE CASCADE

            )

        """)





        # -------------------------------------------------
        # ERROR KNOWLEDGE TABLE
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_knowledge (
                id INT AUTO_INCREMENT PRIMARY KEY,
                language VARCHAR(50) NOT NULL,
                error_type VARCHAR(100) NOT NULL,
                error_pattern TEXT,
                cause TEXT NOT NULL,
                solution TEXT NOT NULL,
                example_code TEXT,
                fixed_code TEXT,
                UNIQUE KEY unique_error (language, error_type)
            )
        """)

        error_records = [
            (
                "Python", "TypeError", "TypeError",
                "Different data types are being used in an incompatible operation.",
                "Convert the values to compatible data types.",
                'age = 20\nmessage = "Age: " + age',
                'age = 20\nmessage = "Age: " + str(age)'
            ),
            (
                "Python", "NameError", "NameError",
                "A variable or function is being used before it is defined.",
                "Check the spelling and define the variable or function before using it.",
                'name = "Dipti"\nprint(username)',
                'name = "Dipti"\nprint(name)'
            ),
            (
                "Python", "ZeroDivisionError", "ZeroDivisionError",
                "The program is trying to divide a number by zero.",
                "Check that the denominator is not zero before division.",
                'a = 10\nb = 0\nprint(a / b)',
                'a = 10\nb = 2\nprint(a / b)'
            ),
            (
                "Python", "IndexError", "IndexError",
                "The program is accessing an index outside the valid range.",
                "Check the length of the list before accessing the index.",
                'numbers = [10, 20, 30]\nprint(numbers[5])',
                'numbers = [10, 20, 30]\nprint(numbers[2])'
            ),
            (
                "Python", "KeyError", "KeyError",
                "The requested dictionary key does not exist.",
                "Check the dictionary key or use get() with a default value.",
                'student = {"name": "Dipti"}\nprint(student["age"])',
                'student = {"name": "Dipti"}\nprint(student.get("age"))'
            ),
            (
                "Python", "ValueError", "ValueError",
                "The program received a value of the correct type but an invalid value.",
                "Check the value and its expected format before using it.",
                'number = int("abc")',
                'number = int("123")'
            ),
            (
                "Python", "AttributeError", "AttributeError",
                "The object does not contain the attribute or method being used.",
                "Check the object type and the spelling of the attribute or method.",
                'name = "Dipti"\nname.append("K")',
                'names = ["Dipti"]\nnames.append("K")'
            ),
            (
                "Python", "ModuleNotFoundError", "ModuleNotFoundError",
                "The required Python module is not installed or the module name is incorrect.",
                "Check the module name and install the required package if necessary.",
                'import unknown_module',
                'import math'
            ),
            (
                "Python", "SyntaxError", "SyntaxError",
                "The Python code contains invalid syntax.",
                "Check the reported line for missing colons, brackets, quotes, or other syntax problems.",
                'def greet(name)\n    print("Hello", name)',
                'def greet(name):\n    print("Hello", name)'
            )
        ]

        cursor.executemany("""
            INSERT IGNORE INTO error_knowledge
            (language, error_type, error_pattern, cause, solution, example_code, fixed_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, error_records)

        connection.commit()



        cursor.close()

        connection.close()



        print("Database initialized successfully.")



    except Error as e:



        print("Database initialization error:", e)





# =========================================================

# LOGIN REQUIRED

# =========================================================



def is_logged_in():



    return (

        "user_id" in session and

        "username" in session

    )





# =========================================================

# HOME PAGE

# =========================================================



@app.route("/")

def home():



    return send_from_directory(

        FRONTEND_DIR,

        "login.html"

    )





# =========================================================

# FRONTEND FILES

# =========================================================



@app.route("/<path:filename>")

def frontend_files(filename):



    return send_from_directory(

        FRONTEND_DIR,

        filename

    )





# =========================================================

# REGISTER

# =========================================================



@app.route("/api/register", methods=["POST"])

def register():



    data = request.get_json()



    if not data:



        return jsonify({

            "success": False,

            "message": "Invalid request."

        })





    username = data.get("username", "").strip()

    password = data.get("password", "")

    confirm_password = data.get(

        "confirm_password",

        ""

    )





    # Username validation

    if not username:



        return jsonify({

            "success": False,

            "message": "Username is required."

        })





    if len(username) < 3:



        return jsonify({

            "success": False,

            "message": "Username must contain at least 3 characters."

        })





    # Password validation

    if not password:



        return jsonify({

            "success": False,

            "message": "Password is required."

        })





    if len(password) < 4:



        return jsonify({

            "success": False,

            "message": "Password must contain at least 4 characters."

        })





    if password != confirm_password:



        return jsonify({

            "success": False,

            "message": "Passwords do not match."

        })





    connection = get_db_connection()



    if connection is None:



        return jsonify({

            "success": False,

            "message": "Database connection failed."

        })





    cursor = connection.cursor()





    try:



        cursor.execute(

            """

            SELECT id

            FROM users

            WHERE username = %s

            """,

            (username,)

        )



        existing_user = cursor.fetchone()





        if existing_user:



            return jsonify({

                "success": False,

                "message": "Username already exists."

            })





        hashed_password = generate_password_hash(

            password

        )





        cursor.execute(

            """

            INSERT INTO users

            (username, password)

            VALUES (%s, %s)

            """,

            (

                username,

                hashed_password

            )

        )





        connection.commit()





        return jsonify({

            "success": True,

            "message": "Account created successfully."

        })





    except Error as e:



        connection.rollback()



        print("Registration error:", e)



        return jsonify({

            "success": False,

            "message": "Unable to create account."

        })





    finally:



        cursor.close()

        connection.close()





# =========================================================

# LOGIN

# =========================================================



@app.route("/api/login", methods=["POST"])

def login():



    data = request.get_json()



    if not data:



        return jsonify({

            "success": False,

            "message": "Invalid request."

        })





    username = data.get(

        "username",

        ""

    ).strip()



    password = data.get(

        "password",

        ""

    )





    if not username or not password:



        return jsonify({

            "success": False,

            "message": "Username and password are required."

        })





    connection = get_db_connection()



    if connection is None:



        return jsonify({

            "success": False,

            "message": "Database connection failed."

        })





    cursor = connection.cursor(

        dictionary=True

    )





    try:



        cursor.execute(

            """

            SELECT id, username, password

            FROM users

            WHERE username = %s

            """,

            (username,)

        )





        user = cursor.fetchone()





        if not user:



            return jsonify({

                "success": False,

                "message": "Invalid username or password."

            })





        if not check_password_hash(

            user["password"],

            password

        ):



            return jsonify({

                "success": False,

                "message": "Invalid username or password."

            })





        # Store session

        session["user_id"] = user["id"]

        session["username"] = user["username"]





        return jsonify({

            "success": True,

            "username": user["username"]

        })





    except Error as e:



        print("Login error:", e)



        return jsonify({

            "success": False,

            "message": "Login failed."

        })





    finally:



        cursor.close()

        connection.close()





# =========================================================

# CURRENT USER

# =========================================================



@app.route("/api/current-user", methods=["GET"])

def current_user():



    if not is_logged_in():



        return jsonify({

            "logged_in": False

        })





    return jsonify({

        "logged_in": True,

        "username": session["username"]

    })





# =========================================================

# LOGOUT

# =========================================================



@app.route("/api/logout", methods=["POST"])

def logout():



    session.clear()



    return jsonify({

        "success": True

    })





# =========================================================

# CODE ANALYZER

# =========================================================



# =========================================================

# CODE ANALYZER

# =========================================================



def analyze_code(language, code):

    language = language.strip()
    code = code.strip()

    if not code:
        return (
            "No code provided.",
            "Enter some code before running the diagnostic check."
        )

    def database_result(error_type, fallback_solution):
        knowledge = get_error_knowledge(language, error_type)

        if knowledge:
            solution = "Cause: " + knowledge["cause"] + "\n\nSuggestion: " + knowledge["solution"]

            if knowledge.get("example_code"):
                solution += "\n\nExample Code:\n" + knowledge["example_code"]

            if knowledge.get("fixed_code"):
                solution += "\n\nFixed Code:\n" + knowledge["fixed_code"]

            return solution

        return fallback_solution

    # =====================================================
    # PYTHON
    # =====================================================

    if language == "Python":

        try:
            ast.parse(code)

        except SyntaxError as e:
            error_message = e.msg or "Invalid Python syntax."
            solution = database_result(
                "SyntaxError",
                "Check the Python syntax and correct the error."
            )

            if e.lineno:
                solution = "Check line " + str(e.lineno) + ".\n\n" + solution

            return (
                "SyntaxError: " + error_message,
                solution
            )

        temp_file = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8"
            ) as file:
                file.write(code)
                temp_file = file.name

            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                error_output = result.stderr.strip()

                error_types = [
                    "TypeError",
                    "NameError",
                    "ZeroDivisionError",
                    "IndexError",
                    "KeyError",
                    "ValueError",
                    "AttributeError",
                    "ModuleNotFoundError"
                ]

                for error_type in error_types:
                    if error_type in error_output:
                        return (
                            error_type + " detected.",
                            database_result(
                                error_type,
                                "The error was detected, but no matching knowledge-base entry was found."
                            )
                        )

                last_line = error_output.splitlines()[-1] if error_output else "Unknown runtime error."

                return (
                    "Runtime error detected.",
                    last_line
                )

            return (
                "No error detected.",
                "The Python code passed both syntax and runtime diagnostic checks."
            )

        except subprocess.TimeoutExpired:
            return (
                "Execution timeout detected.",
                "The program took too long to finish. Check for an infinite loop or very long operation."
            )

        except Exception as e:
            return (
                "Analyzer error.",
                "Unable to complete the diagnostic check: " + str(e)
            )

        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    # =====================================================
    # C++
    # =====================================================

    if language == "C++":
        if code.count("{") != code.count("}"):
            return (
                "Unmatched curly braces detected.",
                "Check that every opening '{' has a corresponding closing '}'."
            )

        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("cout") or "std::cout" in stripped:
                if not stripped.endswith(";"):
                    return (
                        "Missing semicolon in C++ output statement.",
                        "Add ';' at the end of the cout statement."
                    )

        return (
            "No common C++ syntax error detected.",
            "The code passed the basic NeuroPrompt diagnostic checks."
        )

    # =====================================================
    # C
    # =====================================================

    if language == "C":
        if code.count("{") != code.count("}"):
            return (
                "Unmatched curly braces detected.",
                "Check that every opening '{' has a matching closing '}'."
            )

        for line in code.splitlines():
            stripped = line.strip()
            if "printf(" in stripped and not stripped.endswith(";"):
                return (
                    "Possible missing semicolon in printf statement.",
                    "Add ';' at the end of the printf statement."
                )

        return (
            "No common C syntax error detected.",
            "The code passed the basic NeuroPrompt diagnostic checks."
        )

    # =====================================================
    # JAVA
    # =====================================================

    if language == "Java":
        if code.count("{") != code.count("}"):
            return (
                "Unmatched curly braces detected.",
                "Check that every opening '{' has a matching closing '}'."
            )

        for line in code.splitlines():
            stripped = line.strip()
            if "System.out.println" in stripped or "System.out.print" in stripped:
                if not stripped.endswith(";"):
                    return (
                        "Missing semicolon in Java output statement.",
                        "Add ';' at the end of the System.out statement."
                    )

        return (
            "No common Java syntax error detected.",
            "The code passed the basic NeuroPrompt diagnostic checks."
        )

    return (
        "Unsupported language.",
        "Select Python, C++, C, or Java."
    )

@app.route("/api/analyze", methods=["POST"])

def run_analyzer():



    if not is_logged_in():



        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401





    data = request.get_json()





    if not data:



        return jsonify({

            "success": False,

            "message": "Invalid request."

        })





    language = data.get(

        "language",

        ""

    )



    code = data.get(

        "code",

        ""

    )





    error_text, solution_text = analyze_code(

        language,

        code

    )





    connection = get_db_connection()





    if connection is not None:



        cursor = connection.cursor()





        try:



            cursor.execute(

                """

                INSERT INTO analysis_history

                (

                    user_id,

                    language,

                    code_input,

                    detected_error,

                    solution

                )

                VALUES (%s, %s, %s, %s, %s)

                """,

                (

                    session["user_id"],

                    language,

                    code,

                    error_text,

                    solution_text

                )

            )





            connection.commit()





        except Error as e:



            print(

                "History save error:",

                e

            )



        finally:



            cursor.close()

            connection.close()





    return jsonify({

        "success": True,

        "error": error_text,

        "solution": solution_text

    })





# =========================================================

# GET TEMPLATES

# =========================================================



@app.route("/api/templates", methods=["GET"])

def get_templates():



    if not is_logged_in():



        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401





    connection = get_db_connection()



    if connection is None:



        return jsonify({

            "success": False,

            "message": "Database connection failed."

        })





    cursor = connection.cursor(

        dictionary=True

    )





    try:



        cursor.execute(

            """

            SELECT

                id,

                title,

                language,

                code As body,

                created_at

            FROM prompt_templates

            WHERE user_id = %s

            ORDER BY id DESC

            """,

            (session["user_id"],)

        )





        templates = cursor.fetchall()





        return jsonify({

            "success": True,

            "templates": templates

        })





    except Error as e:



        print("Template loading error:", e)



        return jsonify({

            "success": False,

            "message": "Unable to load templates."

        })





    finally:



        cursor.close()

        connection.close()





# =========================================================

# ADD TEMPLATE

# =========================================================



@app.route("/api/templates", methods=["POST"])

def add_template():



    if not is_logged_in():



        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401





    data = request.get_json()





    title = data.get(

        "title",

        ""

    ).strip()



    language = data.get(

        "language",

        ""

    ).strip()



    body = data.get(

        "body",

        ""

    ).strip()





    if not title or not language or not body:



        return jsonify({

            "success": False,

            "message": "All fields are required."

        })





    connection = get_db_connection()



    if connection is None:



        return jsonify({

            "success": False,

            "message": "Database connection failed."

        })





    cursor = connection.cursor()





    try:



        cursor.execute(

            """

            INSERT INTO prompt_templates

            (

                user_id,
                username,
    

                title,

                language,

                code

            )

            VALUES (%s, %s, %s, %s, %s)

            """,

            (

                session["user_id"],
                session["username"],

                title,

                language,

                body

            )

        )





        connection.commit()





        return jsonify({

            "success": True,

            "message": "Template saved successfully."

        })





    except Error as e:



        connection.rollback()



        print("Template save error:", e)



        return jsonify({

            "success": False,

            "message": "Unable to save template."

        })





    finally:



        cursor.close()

        connection.close()

@app.route("/api/templates/<int:template_id>", methods=["PUT"])
def update_template(template_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    data = request.get_json()

    title = data.get("title", "").strip()
    language = data.get("language", "").strip()
    body = data.get("body", "").strip()

    if not title or not language or not body:
        return jsonify({
            "success": False,
            "message": "All fields are required."
        })

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        })

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE prompt_templates
        SET title = %s,
            language = %s,
            code = %s
        WHERE id = %s
        AND user_id = %s
        """,
        (
            title,
            language,
            body,
            template_id,
            session["user_id"]
        )
    )

    connection.commit()

    if cursor.rowcount == 0:
        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": "Template not found."
        })

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Template updated successfully."
    })
  


# =========================================================

# HISTORY

# =========================================================


# =========================================================
# DIAGNOSTIC HISTORY
# =========================================================

# =========================================================
# DIAGNOSTIC HISTORY
# =========================================================

# =========================================================
# DIAGNOSTIC HISTORY
# =========================================================

@app.route("/api/history", methods=["GET"])
def get_history():

    if not is_logged_in():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    connection = get_db_connection()

    if connection is None:

        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500


    cursor = connection.cursor(dictionary=True)


    try:

        cursor.execute(
            """
            SELECT
                id,
                language,
                code_input,
                detected_error,
                solution
            FROM analysis_history
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (
                session["user_id"],
            )
        )


        history = cursor.fetchall()


        return jsonify({
            "success": True,
            "history": history
        })


    except Error as e:

        print(
            "DIAGNOSTIC HISTORY ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to load diagnostic history.",
            "error": str(e)
        }), 500


    finally:

        cursor.close()
        connection.close()

# =========================================================

# START APPLICATION

# =========================================================



if __name__ == "__main__":



    initialize_database()



    print("")

    print("==========================================")

    print("       NeuroPrompt Flask Application")

    print("==========================================")

    print("Open: http\://127.0.0.1:5000/")

    print("==========================================")

    print("")



    app.run(

        debug=True

    )