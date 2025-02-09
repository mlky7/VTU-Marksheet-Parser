# VTU Marksheet Parser

A web-based application that allows users to upload their VTU mark sheets in PDF format, automatically extracts marks, and fills the SGPA calculator input fields. The extracted data (marks, credits, and subject codes) is stored in MongoDB, supporting 3rd to 5th semesters of the 2022 scheme, with scalability for additional semesters and subjects in the future.

## Features
- **Upload VTU Marksheet**: Users can upload their VTU marksheet in PDF format.
- **Automatic Mark Extraction**: The parser, implemented using `pdfplumber`, reads marks directly from the PDF.
- **SGPA Auto-Fill & Calculation**: Extracted marks are mapped to the respective subject codes, filling the SGPA calculator automatically.
- **CGPA Calculation Page**: Users can also compute their cumulative GPA (CGPA).
- **MongoDB Integration**: Stores subject codes, credits, and marks for 3rd to 5th semesters (2022 scheme), allowing easy expansion in the future.
- **Flask Backend**: The project runs on a Flask server, handling PDF parsing and database operations.

## Tech Stack
- **Backend**: Flask, pdfplumber, MongoDB
- **Frontend**: HTML, CSS, JavaScript (if applicable)
- **Database**: MongoDB
