import datetime

class Logger:
    @staticmethod
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.unseensuspiciouslogs = []

    @staticmethod
    def writelog(self, username, whathappened, extradetails="", issuspicious=False):
        if not self.db_manager:
            print("Logger cant write, no database connection.")
            return

        currenttime = datetime.datetime.now().isoformat()
        try:
            self.db_manager.addnewrecord(
                'logs',
                {
                    'timestamp': currenttime,
                    'username': username,
                    'description': whathappened,
                    'additional_info': extradetails,
                    'suspicious': 1 if issuspicious else 0
                }
            )
            if issuspicious:
                print(f"WARNING: suspicious activity detected. sending missile to {username}")
                self.unseensuspiciouslogs.append(
                    f"Suspicious activity detected on user account {username} at {currenttime}: {whathappened}")
        except Exception as e:
            print(f"couldn't write log. Error: {e}")
   
    @staticmethod
    def getlogs(self):
        if not self.db_manager:
            print("Cant get logs.")
            return []
        return self.db_manager.getdata('logs')

    @staticmethod
    def show_logs_to_admin(self) -> None:
        alllogs = self.getlogs()
        if not alllogs:
            print("No logs to show right now.")
            return

        print("\n--- All System Logs ---")
        for logentry in alllogs:
            suspicioustag = "[SUSPICIOUS] " if logentry.get('suspicious') == 1 else ""
            print(
                f"[{logentry.get('timestamp')}] {suspicioustag}{logentry.get('username')}: {logentry.get('description')} ({logentry.get('additional_info')})")

        if self.unseensuspiciouslogs:
            print("\nAll suspicious alerts have been seen by an admin.")
            self.unseensuspiciouslogs.clear()