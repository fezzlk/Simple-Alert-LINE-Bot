from .LineUserRepository import LineUserRepository
from .StockRepository import StockRepository
from .WebUserRepository import WebUserRepository
from .HabitTaskRepository import HabitTaskRepository
from .HabitTaskLogRepository import HabitTaskLogRepository
from .HabitPendingConfirmationRepository import HabitPendingConfirmationRepository

web_user_repository = WebUserRepository()
line_user_repository = LineUserRepository()
stock_repository = StockRepository()
habit_task_repository = HabitTaskRepository()
habit_task_log_repository = HabitTaskLogRepository()
habit_pending_confirmation_repository = HabitPendingConfirmationRepository()
