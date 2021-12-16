from .Line.FollowUseCase import FollowUseCase
from .Line.UnfollowUseCase import UnfollowUseCase
from .Line.JoinUseCase import JoinUseCase

from .Line.TextMessageUseCase import TextMessageUseCase
from .Line.ImageMessageUseCase import ImageMessageUseCase
from .Line.PostbackUseCase import PostbackUseCase

from .Line.ReplyTrainDelayUseCase import ReplyTrainDelayUseCase

from .Line.ReplyWeatherUseCase import ReplyWeatherUseCase
from .Web.ViewWeatherUseCase import ViewWeatherUseCase

from .Stock.RegisterStockUseCase import RegisterStockUseCase
from .Stock.ReplyStockUseCase import ReplyStockUseCase

from .Line.RequestLinkLineWebUseCase import RequestLinkLineWebUseCase

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

request_link_line_web_use_case = RequestLinkLineWebUseCase()
