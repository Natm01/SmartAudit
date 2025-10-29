import pyodbc
import sys
import time


class AccountingDataLoader:
    """
    Simplified loader for staging data.
    Calls stored procedures that handle all loading, validation, and processing internally.
    """

    def __init__(self, execution_id: str, auth_user_id: int = 1):
        """
        Initialize loader with execution ID and user ID.

        Args:
            execution_id: The je_analysis_exec_gid (UNIQUEIDENTIFIER)
            auth_user_id: The authenticated user ID (default: 1)
        """
        self.execution_id = execution_id
        self.auth_user_id = auth_user_id

        self.CONNECTION_STRING = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=smau-dev-sql.database.windows.net;"
            "DATABASE=smau-dev-sqldb;"
            "UID=smau_dev_user;"
            "PWD=x+4Cj5Gdnml*NfwujyENmUeeNxYz8kw-N_e4EeI6FRkI+;"
            "Encrypt=yes;TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

    def load_staging(self, conn):
        """
        Load data to staging using stored procedures.
        Each SP receives only auth_user_id and je_analysis_exec_gid.
        The SPs handle internally:
        - Resolving dataset_version_id from execution_id
        - Finding blob paths
        - Data validation
        - Loading data
        """
        cursor = conn.cursor()

        print("=" * 80)
        print("LOADING DATA TO STAGING")
        print("=" * 80)
        print(f"Execution ID (je_analysis_exec_gid): {self.execution_id}")
        print(f"Auth User ID: {self.auth_user_id}")
        print("-" * 80)

        try:
            # === Journal Entries ===
            print("\n[1/3] Loading Journal Entries...")
            self._execute_sp(
                cursor,
                conn,
                sp_name="staging.sp_load_journal_entries_csv_from_blob",
                file_type="JOURNAL ENTRIES"
            )

            # === Journal Entry Lines ===
            print("\n[2/3] Loading Journal Entry Lines...")
            self._execute_sp(
                cursor,
                conn,
                sp_name="staging.sp_load_journal_entry_lines_csv_from_blob",
                file_type="JOURNAL ENTRY LINES"
            )

            # === Trial Balance ===
            print("\n[3/3] Loading Trial Balance...")
            self._execute_sp(
                cursor,
                conn,
                sp_name="staging.sp_load_trial_balance_csv_from_blob",
                file_type="TRIAL BALANCE"
            )

            print("\n" + "=" * 80)
            print("✓ ALL DATA LOADED SUCCESSFULLY TO STAGING")
            print("=" * 80)

        except Exception as e:
            conn.rollback()
            print("\n" + "=" * 80)
            print("✗ ERROR LOADING STAGING")
            print("=" * 80)
            raise Exception(f"Error loading staging: {str(e)}")

    def _execute_sp(self, cursor, conn, sp_name: str, file_type: str):
        """
        Execute a stored procedure and display results.

        Args:
            cursor: Database cursor
            conn: Database connection
            sp_name: Name of the stored procedure
            file_type: Description of the file type being loaded
        """
        print(f"Executing: {sp_name}")

        try:
            cursor.execute(f"""
                EXEC {sp_name}
                    @auth_user_id = ?,
                    @je_analysis_exec_gid = ?
            """, (self.auth_user_id, self.execution_id))

            # Try to capture result if SP returns one
            try:
                result = cursor.fetchone()
                if result:
                    print("RESULT:")
                    # Display all columns returned by the SP
                    for idx, column in enumerate(cursor.description):
                        print(f"  {column[0]:25s}: {result[idx]}")
                    print("-" * 80)
            except:
                # Some SPs might not return results
                pass

            conn.commit()
            print(f"✓ {file_type} loaded successfully\n")

        except Exception as e:
            print(f"✗ Error loading {file_type}: {str(e)}")
            raise

    def process_data_load(self):
        """
        Main process: connects to database and loads staging data.

        Returns:
            dict: Result with 'success' boolean and optional 'error' message
        """
        print("=" * 80)
        print("STARTING DATA LOAD PROCESS")
        print("=" * 80)
        print(f"Execution ID: {self.execution_id}")
        print(f"Auth User ID: {self.auth_user_id}")
        print("=" * 80)

        conn = None
        start_time = time.time()

        try:
            # Connect to database
            conn = pyodbc.connect(self.CONNECTION_STRING)
            print("✓ Database connection established\n")

            # Load staging data
            self.load_staging(conn)

            elapsed_time = time.time() - start_time
            print("\n" + "=" * 80)
            print(f"✓ PROCESS COMPLETED SUCCESSFULLY in {elapsed_time:.2f}s")
            print("=" * 80)

            return {
                "success": True,
                "elapsed_time": elapsed_time
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"\n✗ Process failed after {elapsed_time:.2f}s: {e}")

            if conn:
                try:
                    conn.rollback()
                except:
                    pass

            return {
                "success": False,
                "error": str(e),
                "elapsed_time": elapsed_time
            }

        finally:
            if conn:
                conn.close()
                print("✓ Database connection closed")


def main():
    """
    Main function for command-line execution.

    Usage:
        python accounting_loader_prod.py <execution_id>

    Example:
        python accounting_loader_prod.py "12345678-1234-1234-1234-123456789012"
    """
    if len(sys.argv) < 2:
        print("Usage: python accounting_loader_prod.py <execution_id>")
        print("Example: python accounting_loader_prod.py '12345678-1234-1234-1234-123456789012'")
        return 1

    execution_id = sys.argv[1]

    # Create loader
    loader = AccountingDataLoader(execution_id=execution_id, auth_user_id=1)

    # Execute process
    result = loader.process_data_load()

    # Return exit code
    if result["success"]:
        print("\n✓ Process completed successfully")
        return 0
    else:
        print(f"\n✗ Process failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
