from task import TaskFactory
from template import TemplateFactory

class TemplateStrategy:
    def __init__(self, action, val):
        self.action = action
        self.val = val
        self.template_map = {
            '開課時間查詢': 'course',
            '證書申請流程': 'certificate',
            '社群學習資源': 'community',
        }

    def strategy_action(self):
        strategy_class = None
        templateFactory = TemplateFactory()
        strategy_class = templateFactory.get_template(self.template_map.get(self.val))
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