import enum

# "str, enum.Enum" makes enum values JSON serializable and storable as strings in SQLite
class TaskType(str, enum.Enum):
    ACADEMIC = "academic"
    PERSONAL =  "personal"
    URGENT = "urgent"
    RECURRING = "recurring"
    SOCIAL = "social"
    
    
class RecurrenceType(str, enum.Enum):
    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    