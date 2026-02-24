from src.Infrastructure.Repositories import (
    line_user_repository,
    notification_schedule_repository,
)


def main() -> None:
    line_users = line_user_repository.find()
    for line_user in line_users:
        notification_schedule_repository.upsert(
            line_user_id=line_user.line_user_id,
            notify_time="12:00",
            timezone_name="Asia/Tokyo",
        )
    print(f"backfilled notification_schedules: {len(line_users)}")


if __name__ == "__main__":
    main()
