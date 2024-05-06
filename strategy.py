from task import TaskFactory
from template import TemplateFactory

class TemplateStrategy:
    def __init__(self, action, val):
        self.action = action
        self.val = val

    def strategy_action(self):
        strategy_class = None
        templateFactory = TemplateFactory()
        strategy_class = templateFactory.get_template(self.val)
        return strategy_class

class TaskStrategy:
    def __init__(self, action, val):
        self.action = action
        self.val = val

    def strategy_action(self):
        strategy_class = None
        taskFactory = TaskFactory()
        if self.action == 'postback':
            strategy_class = taskFactory.get_task(self.val.get('task'))
        else:
            strategy_class = taskFactory.get_task(self.val)
        return strategy_class