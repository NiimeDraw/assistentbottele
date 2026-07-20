"""Definisi FSM States (finite state machine) untuk alur input multi-step."""
from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    waiting_title = State()
    waiting_deadline = State()
    waiting_description = State()


class ScheduleStates(StatesGroup):
    waiting_mata_kuliah = State()
    waiting_hari = State()
    waiting_jam_mulai = State()
    waiting_jam_selesai = State()
    waiting_ruangan = State()
    waiting_dosen = State()
    waiting_reminder = State()


class NoteStates(StatesGroup):
    waiting_title = State()
    waiting_content = State()


class AIStates(StatesGroup):
    waiting_question = State()


class UserStates(StatesGroup):
    waiting_fakultas = State()
    waiting_jurusan = State()
    waiting_angkatan = State()
    waiting_semester = State()
    confirm_delete = State()
