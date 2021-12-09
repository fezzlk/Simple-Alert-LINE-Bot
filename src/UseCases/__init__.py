from .AfterLoginUseCase import AfterLoginUseCase

from .FollowUseCase import FollowUseCase
from .UnfollowUseCase import UnfollowUseCase
from .JoinUseCase import JoinUseCase

from .TextMessageUseCase import TextMessageUseCase
from .ImageMessageUseCase import ImageMessageUseCase
from .PostbackUseCase import PostbackUseCase

from .ReplyTrainDelayUseCase import ReplyTrainDelayUseCase

from .ReplyWeatherUseCase import ReplyWeatherUseCase
from .ViewWeatherUseCase import ViewWeatherUseCase

from .Stock.RegisterStockUseCase import RegisterStockUseCase
from .Stock.ReplyStockUseCase import ReplyStockUseCase

after_login_use_case = AfterLoginUseCase()

follow_use_case = FollowUseCase()
unfollow_use_case = UnfollowUseCase()
join_use_case = JoinUseCase()

text_message_use_case = TextMessageUseCase()
image_message_use_case = ImageMessageUseCase()
postback_use_case = PostbackUseCase()

reply_train_delay_use_case = ReplyTrainDelayUseCase()

reply_weather_use_case = ReplyWeatherUseCase()
view_weather_use_case = ViewWeatherUseCase()

register_stock_use_case = RegisterStockUseCase()
reply_stock_use_case = ReplyStockUseCase()
