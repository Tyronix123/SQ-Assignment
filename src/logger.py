from datetime import datetime
from db_handler import DBHandler

class Logger:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler
        self.unseensuspiciouslogs = []

    def writelog(self, username, activity, details="", issuspicious=False):
        if not self.db_handler:
            print("Logger cant write, no database connection.")
            return

        currenttime = datetime.now().isoformat()
        try:
            self.db_handler.addnewrecord(
                'logs',
                {
                    'time': currenttime,
                    'username': username,
                    'activity': activity,
                    'details': details,
                    'suspicious': 1 if issuspicious else 0
                }
            )
            if issuspicious:
                print(f"WARNING: suspicious activity detected. sending missile to {username}")
                self.unseensuspiciouslogs.append(
                    f"Suspicious activity detected on user account {username} at {currenttime}: {activity}")
        except Exception as e:
            print(f"couldn't write log. Error: {e}")
   
    def getlogs(self):
        if not self.db_handler:
            print("Cant get logs.")
            return []
        return self.db_handler.getdata('logs')


    def show_logs_to_admin(self) -> None:
        alllogs = self.getlogs()
        if not alllogs:
            print("No logs to show right now.")
            return

        print("\n--- All System Logs ---")
        for logentry in alllogs:
            suspicioustag = "[SUSPICIOUS] " if logentry.get('suspicious') == 1 else ""

            raw_time = logentry.get('time')
            try:
                parsed_time = datetime.fromisoformat(raw_time)
                formatted_time = parsed_time.strftime('%d-%m-%Y %H:%M:%S')
            except Exception:
                formatted_time = raw_time

            log_line = f"[{formatted_time}] {suspicioustag}{logentry.get('username')}: {logentry.get('activity')}"
            details = logentry.get('details')
            if details:
                log_line += f" ({details})"

            print(log_line)

        if self.unseensuspiciouslogs:
            print("\nAll suspicious alerts have been seen by an admin.")
            self.unseensuspiciouslogs.clear()