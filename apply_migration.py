"""
Script to manually add the use_rag column to the database.
Run this with: python apply_migration.py
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

print(f"Connecting to database: {db_path}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(assignment_assignment)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'use_rag' in columns:
        print("✓ Column 'use_rag' already exists in assignment_assignment table")
    else:
        print("Adding 'use_rag' column to assignment_assignment table...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE assignment_assignment 
            ADD COLUMN use_rag INTEGER DEFAULT 1 NOT NULL
        """)
        
        conn.commit()
        print("✓ Column 'use_rag' added successfully!")
    
    # Verify
    cursor.execute("PRAGMA table_info(assignment_assignment)")
    columns = cursor.fetchall()
    print(f"\nCurrent columns in assignment_assignment table:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    print("\n✓ Migration completed successfully!")
    
except sqlite3.Error as e:
    print(f"✗ Database error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
