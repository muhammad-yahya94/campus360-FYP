import pandas as pd


def clean_excel_columns(file):
    """
    This function reads the Excel file, detects the correct header row,
    cleans the columns (stripping spaces, converting to lowercase),
    checks for required columns, and identifies gaps in student data.
    """
    # Step 1: Read the Excel file without assuming header rows
    df = pd.read_excel(file, engine='openpyxl', header=None)

    # Step 2: Identify the first row that seems to be the header
    header_row_index = None
    for i, row in df.iterrows():
        if 'roll#' in row.str.lower().values:
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("Could not find a valid header row.")

    # Step 3: Set the identified row as the header and clean up columns
    df.columns = df.iloc[header_row_index].str.strip().str.lower()

    # Step 4: Drop all rows before the header row
    df = df.drop(index=range(header_row_index + 1))

    # Step 5: Strip spaces from all column names
    df.columns = df.columns.str.strip()

    # Step 6: Check for missing required columns
    required_columns = [
        'sr#', 'roll#', 'student name', 'student father name', 'student cnic',
        'session', 'attempt', 'internal marks (6)', 'mid term marks (12)',
        'final term marks (42)', 'practical work (0)', 'total obtain marks',
        'marks %age', 'grade', 'student status'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    # Step 7: Check for gaps in student rows (e.g., missing roll# or student name)
    # Instead of dropping, flag the rows with missing essential data
    gap_rows = df[df['roll#'].isna() | df['student name'].isna()]

    if not gap_rows.empty:
        print(f"Warning: There are gaps in the following rows (missing roll# or student name):")
        print(gap_rows[['sr#', 'roll#', 'student name']])

    # Optionally, you can mark or handle rows with gaps (for example, by filling them with placeholders or leaving them)
    # For now, we'll simply print the rows and not remove them.

    # Returning the cleaned DataFrame with all data (even those with gaps)
    return df