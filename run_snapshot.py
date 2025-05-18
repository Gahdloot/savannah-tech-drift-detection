from src.collector import get_users, save_snapshot

if __name__ == "__main__":
    data = get_users()
    file_path = save_snapshot(data, label="users")
    print(f"Snapshot saved to {file_path}")