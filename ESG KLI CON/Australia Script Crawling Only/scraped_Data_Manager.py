import datetime

class ScrapedDataManager:
    def __init__(self, file_name):
        """Initialize the manager with the file name and load existing article IDs."""
        self.file_name = file_name
        self.scraped_comm_sch = self._load_scraped_comm_sch()

    def _load_scraped_comm_sch(self):
        """Private method to load scraped committee sched from the file."""
        """Private method to load scraped article IDs and their dates from the file."""
        scraped_data = {}
        try:
            with open(self.file_name, 'r') as file:
                for line in file:
                    comm_sch, date_saved = line.strip().split('\t')
                    scraped_data[comm_sch] = date_saved  # Store date with ID
        except FileNotFoundError:
            return {}
        return scraped_data

    def save_data_to_logs(self, comm_sch):
        """Save a new committee sched to the file and add it to the in-memory set."""
        if comm_sch not in self.scraped_comm_sch:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.file_name, 'a') as file:
                file.write(f"{comm_sch}\t{current_date}\n")
            self.scraped_comm_sch[comm_sch] = current_date
            print("New Record saved...")

    def is_already_scraped(self, comm_sch):
        """Check if an committee sched has already been scraped."""
        return comm_sch in self.scraped_comm_sch
