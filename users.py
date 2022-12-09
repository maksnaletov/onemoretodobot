import time
import tasks

COMMANDS = {
    '/new': 'COMMAND_NEW',
    '/tasks': 'COMMAND_TASKS',
    '/closed_tasks': 'COMMAND_CLOSED_TASKS',
    '/close': 'COMMAND_CLOSE'
}

class UserState:

    def __init__(self, user_id, state):
        self._user_id = user_id
        if state in COMMANDS:
            self._state = COMMANDS[state]
            self.is_terminated = False
        else:
            self.is_terminated = True
        self.reply_text = ''
        

    def process_state(self, msg):

        if self.is_terminated:
            return

        if self._state == 'COMMAND_NEW':
            self._state = 'WAIT_FOR_TITLE'
            self.reply_text = 'Пришли текст задачи'
            return

        if self._state == 'WAIT_FOR_TITLE':
            self._state = 'CONFIRM_EDITING'
            self._task = tasks.create_task(self._user_id, msg)
            self.reply_text = 'Задача создана. Добавить описание и напоминание?'
            return
        
        if self._state == 'CONFIRM_EDITING':
            if msg.lower() in ('нет', 'no', '-'):
                self.is_terminated = True
                self.reply_text = ''
            if msg.lower() in ('да', 'yes', '+'):
                self._state = 'SET_DESCRIPTION'
                self.reply_text = 'Добавь описание или пришли "-"'
            return
        
        if self._state == 'SET_DESCRIPTION':
            if msg != '-':
                tasks.update_field(self._user_id, self._task, 'DESCRIPTION', msg)
            self._state = 'SET_REMINDER'
            self.reply_text = 'Напиши дату и время напоминания (по Москве) в формате ДД.ММ.ГГГГ ЧЧ:ММ или пришли "-"'
            return

        if self._state == 'SET_REMINDER':
            if msg != '-':
                try:
                    reminder_timestamp = str(int(time.mktime(time.strptime(msg + ' +0300', '%d.%m.%Y %H:%M %z'))))
                except ValueError:
                    self.reply_text = 'Дата и время не распознаны. Напиши дату и время напоминания в формате ДД.ММ.ГГГГ ЧЧ:ММ или пришли "-"'
                    return
                tasks.update_field(self._user_id, self._task, 'REMIND_TS', reminder_timestamp)
            self.is_terminated = True
            self.reply_text = 'Задача создана'
            return

        if self._state == 'COMMAND_TASKS':
            self.is_terminated = True
            task_list = tasks.get_task_list(self._user_id)
            self.reply_text = task_list
            return
        
        if self._state == 'COMMAND_CLOSED_TASKS':
            self.is_terminated = True
            task_list = tasks.get_task_list(self._user_id, mode='closed')
            self.reply_text = task_list
            return

        if self._state == 'COMMAND_CLOSE':
            self._state = 'CHOOSE_TASK'
            head = 'Введи номер выполненной задачи или "-". Актуальные задачи:\n\n'
            task_list = tasks.get_task_list(self._user_id)
            self.reply_text = head + task_list
            return

        if self._state == 'CHOOSE_TASK':
            if msg != '-':
                try:
                    task_id = int(msg)
                except ValueError:
                    self.reply_text = 'Нет адачи с таким номером. Введи номер выполненной задачи или "-"'
                    return
                close_result = tasks.update_field(self._user_id, task_id, 'STATUS', 'CLOSED')
                if close_result == 0:
                    self.reply_text = 'Нет адачи с таким номером. Введи номер выполненной задачи или "-"'
                    return
                self.reply_text = 'Задача выполнена. Ура!'
            self.is_terminated = True
