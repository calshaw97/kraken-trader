"""
Claw's Self-Scheduler
Allows me to create my own wake-up calls dynamically

Examples:
- "Check this trade in 5 minutes"
- "Follow up on this opportunity in 2 hours"
- "Monitor this event for the next 30 minutes (every 5 min)"
"""

import json
import subprocess
from datetime import datetime, timedelta

class SelfScheduler:
    """Tool for creating dynamic cron jobs"""
    
    def __init__(self):
        self.log_path = r"C:\Users\Sya\Documents\Clawd_Brain\10_Projects\Claw_Trading\scheduler_log.md"
    
    def schedule_once(self, minutes_from_now, task_description):
        """
        Schedule a one-time wake-up
        
        Example: schedule_once(5, "Check BTC trade - check if price hit $70k")
        """
        at_time_ms = int((datetime.now() + timedelta(minutes=minutes_from_now)).timestamp() * 1000)
        
        job = {
            "name": f"claw-task-{int(datetime.now().timestamp())}",
            "schedule": {
                "kind": "at",
                "atMs": at_time_ms
            },
            "payload": {
                "kind": "systemEvent",
                "text": f"🔔 SCHEDULED TASK: {task_description}"
            },
            "sessionTarget": "main",
            "enabled": True
        }
        
        # Log the scheduled task
        self._log_task("ONCE", minutes_from_now, task_description, at_time_ms)
        
        return job
    
    def schedule_repeating(self, interval_minutes, duration_minutes, task_description):
        """
        Schedule repeating wake-ups for a limited time
        
        Example: schedule_repeating(5, 30, "Monitor BTC for 30 mins, check every 5")
        This will create a cron that runs every 5 minutes and disables after 30 minutes
        """
        # OpenClaw doesn't have built-in "stop after X duration" so we'll need to:
        # 1. Create the repeating cron
        # 2. Schedule a separate "disable this cron" task
        
        interval_ms = interval_minutes * 60 * 1000
        
        job_name = f"claw-monitor-{int(datetime.now().timestamp())}"
        
        job = {
            "name": job_name,
            "schedule": {
                "kind": "every",
                "everyMs": interval_ms
            },
            "payload": {
                "kind": "systemEvent",
                "text": f"🔁 REPEATING TASK: {task_description}"
            },
            "sessionTarget": "main",
            "enabled": True
        }
        
        # Schedule a task to disable this job after duration
        stop_at_ms = int((datetime.now() + timedelta(minutes=duration_minutes)).timestamp() * 1000)
        
        stop_job = {
            "name": f"claw-stop-{job_name}",
            "schedule": {
                "kind": "at",
                "atMs": stop_at_ms
            },
            "payload": {
                "kind": "systemEvent",
                "text": f"🛑 STOP MONITOR: Disable {job_name}"
            },
            "sessionTarget": "main",
            "enabled": True
        }
        
        self._log_task("REPEATING", f"{interval_minutes}min for {duration_minutes}min", 
                      task_description, stop_at_ms)
        
        return [job, stop_job]
    
    def schedule_progressive(self, intervals_minutes, task_description):
        """
        Schedule progressive checks (e.g., check in 1 min, then 5 min, then 15 min)
        
        Example: schedule_progressive([1, 5, 15, 30], "Progressive monitoring of new position")
        """
        jobs = []
        current_time = datetime.now()
        
        for i, minutes in enumerate(intervals_minutes):
            check_time = current_time + timedelta(minutes=minutes)
            at_time_ms = int(check_time.timestamp() * 1000)
            
            job = {
                "name": f"claw-progressive-{int(current_time.timestamp())}-{i}",
                "schedule": {
                    "kind": "at",
                    "atMs": at_time_ms
                },
                "payload": {
                    "kind": "systemEvent",
                    "text": f"📊 PROGRESSIVE CHECK #{i+1}/{len(intervals_minutes)}: {task_description}"
                },
                "sessionTarget": "main",
                "enabled": True
            }
            jobs.append(job)
        
        self._log_task("PROGRESSIVE", str(intervals_minutes), task_description, at_time_ms)
        
        return jobs
    
    def _log_task(self, task_type, schedule, description, target_ms):
        """Log scheduled task for tracking"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_time = datetime.fromtimestamp(target_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"""
### {timestamp} - Scheduled Task
- **Type:** {task_type}
- **Schedule:** {schedule}
- **Target Time:** {target_time}
- **Task:** {description}

"""
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("# Claw's Self-Scheduler Log\n\n")
                f.write(log_entry)


# Example usage:
if __name__ == "__main__":
    scheduler = SelfScheduler()
    
    print("Self-Scheduler Examples:\n")
    
    # Example 1: One-time check in 5 minutes
    print("1. Schedule single check in 5 minutes:")
    job1 = scheduler.schedule_once(5, "Check if BTC hit $70k target")
    print(json.dumps(job1, indent=2))
    print()
    
    # Example 2: Monitor every 5 minutes for 30 minutes
    print("2. Monitor every 5 min for 30 min:")
    jobs2 = scheduler.schedule_repeating(5, 30, "Watch LTC position closely")
    for job in jobs2:
        print(json.dumps(job, indent=2))
    print()
    
    # Example 3: Progressive checks (1, 5, 15, 30 minutes)
    print("3. Progressive checks after buying:")
    jobs3 = scheduler.schedule_progressive([1, 5, 15, 30], "New BTC position - progressive monitoring")
    for job in jobs3:
        print(json.dumps(job, indent=2)[:200])
    print()
