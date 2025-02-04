from flask import Flask, request, make_response, render_template_string
import re
from AutoCalendarV4 import parseCourses, generateICS

app = Flask(__name__)

# Path to the file that will store the emails.
EMAILS_FILE = "emails.txt"

# HTML template with Tailwind CSS styling, instructions for Outlook, thank-you box, and email input.
form_template = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ICS File Generator</title>
  <!-- Include Tailwind CSS via CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
  <div class="min-h-screen flex flex-col items-center justify-center px-4">
    <!-- Main container for the form -->
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-2xl">
      <h1 class="text-3xl font-bold mb-4 text-center text-blue-600">Course Schedule ICS Generator</h1>
      <p class="mb-6 text-gray-700 text-center">
        Paste your course info below, enter your email, and click the button to download your ICS file.
      </p>
      <!-- Error message display -->
      {% if error %}
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <span class="block sm:inline">{{ error }}</span>
      </div>
      {% endif %}
      <!-- The input form for course info and email -->
      <form method="POST">
        <div class="mb-4">
          <input type="email" name="user_email" required
                 class="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                 placeholder="Enter your email">
        </div>
        <div class="mb-4">
          <textarea name="course_data" rows="10" class="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400" placeholder="Paste your course info here"></textarea>
        </div>
        <div class="mt-6 flex justify-center">
          <button type="submit" class="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400">
            Download ICS File
          </button>
        </div>
      </form>
    </div>

    <!-- Instructions Box for Outlook -->
    <div class="mt-8 w-full max-w-2xl bg-blue-50 border border-blue-200 p-6 rounded-lg shadow-sm">
      <h2 class="text-2xl font-semibold text-blue-700 mb-2">How to Add to Outlook</h2>
      <p class="text-gray-700">
        After downloading the ICS file, open Outlook and follow these steps:
      </p>
      <ol class="list-decimal ml-6 mt-2 text-gray-700">
        <li>Open Outlook.</li>
        <li>Go to <strong>File &gt; Open &amp; Export</strong> and choose <strong>Import/Export</strong>.</li>
        <li>Select <strong>Import an iCalendar (.ics)</strong>.</li>
        <li>Browse and select the downloaded <em>courses.ics</em> file.</li>
        <li>Choose to open as a new calendar or import into your current calendar.</li>
      </ol>
    </div>

    <!-- Thank You Box -->
    <div class="mt-8 w-full max-w-2xl bg-green-50 border border-green-200 p-6 rounded-lg shadow-sm text-center">
      <h2 class="text-2xl font-semibold text-green-700 mb-2">Thank You!</h2>
      <p class="text-gray-700">
        Thank you for using my calendar app.
      </p>
      <p class="mt-4">
        Follow me on Instagram for more projects:
        <a href="https://www.instagram.com/phoenixs.png/" class="text-blue-600 hover:underline" target="_blank">
          @phoenixs.png
        </a>
      </p>
    </div>

    <!-- Footer -->
    <footer class="mt-8 text-gray-500">
      &copy; 2025 Phoenix Stuempel
    </footer>
  </div>
</body>
</html>
"""

# A simple regular expression for basic email validation.
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    The index route handles both GET and POST requests.
    
    - GET: Displays the form along with instructions on how to add the ICS file to Outlook and a thank you message.
    - POST: Validates the provided email, processes the submitted course info, parses the data,
            generates the ICS file, logs the email, and triggers a file download.
    """
    if request.method == 'POST':
        # Retrieve the email and course info from the form.
        user_email = request.form.get('user_email', '').strip()
        input_text = request.form.get('course_data', '')
        # Normalize newlines and remove extra whitespace.
        input_text = input_text.replace("\r\n", "\n").strip()
        
        # Validate the email using a simple regex.
        if not re.match(EMAIL_REGEX, user_email):
            # If email is invalid, re-render the template with an error message.
            error_message = "Please enter a valid email address."
            return render_template_string(form_template, error=error_message)
        
        # Append the valid email to the emails file.
        with open(EMAILS_FILE, "a", encoding="utf-8") as f:
            f.write(user_email + "\n")
        
        # Parse the courses from the input text using the provided function.
        parsedCourses = parseCourses(input_text)
        # Generate the ICS file content using the provided function.
        icsContent = generateICS(parsedCourses)
        
        # Create a response with the ICS content.
        response = make_response(icsContent)
        # Set headers to prompt a file download with the name 'courses.ics'.
        response.headers["Content-Disposition"] = "attachment; filename=courses.ics"
        response.headers["Content-Type"] = "text/calendar"
        return response
    else:
        # Render the HTML form and additional information for GET requests.
        return render_template_string(form_template)

if __name__ == "__main__":
    # Run the Flask development server in debug mode.
    app.run(debug=True)
