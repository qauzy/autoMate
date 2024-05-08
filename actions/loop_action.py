import time

from pydantic import BaseModel, Field

from actions.action_base import ActionBase


class LoopInput(BaseModel):
    # loop_number: int = Field(description="循环次数", title="循环次数", default=0)
    stop_condition: str = Field(description="循环退出条件，python表达式", title="循环退出条件", default="False")
    loop_interval_time: int = Field(description="循环间隔时间，单位是秒", title="循环间隔时间(秒)", default=0)
    # action_list 代表内置参数，会被映射成ActionList对象
    # action_list: list[ActionBase] = Field(description="循环执行的内容", title="循环执行的内容", default=[])


class LoopAction(ActionBase):
    name = "循环执行"
    description = "根据循环条件循环执行"
    args: LoopInput

    def run(self, stop_condition, loop_interval_time):
        while True:
            if eval(stop_condition, {}, self._get_edit_page().get_output_dict()):
                break
            # action_list.run()
            action_list = self.get_data("action_list")
            action_list.run()
            time.sleep(loop_interval_time)
