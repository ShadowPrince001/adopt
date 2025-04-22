from sync_databases import sync_databases
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    sync_databases()

if __name__ == "__main__":
    main() 