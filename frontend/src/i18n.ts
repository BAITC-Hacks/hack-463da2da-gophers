import type { Language } from './api/types'

export const labels = {
  ru: {
    path: 'Мой карьерный путь', myPath: 'Мой путь', hr: 'HR-дашборд', light: 'Светлая тема', dark: 'Тёмная тема', language: 'Язык интерфейса', city: 'Алматы', address: 'пр. Аль-Фараби, 40',
    tenure: 'месяцев в компании', selectEmployee: 'Выбрать сотрудника', goal: 'Цель', noGoal: 'Следующий грейд', trajectory: 'Следующий уровень', radar: 'Зелёный — текущий уровень, золотой контур — требуемый.',
    skills: 'Навыки для следующего уровня', critical: 'Критичный', current: 'сейчас', required: 'требуется', closeGap: 'Как закрыть разрыв', hoursShort: 'ч',
    history: 'История активностей', historyIntro: 'Ваши шаги развития и их результаты', noHistory: 'Активностей пока нет',
    recommendations: 'Рекомендованные шаги', recError: 'Не удалось получить рекомендации. Попробуйте снова.', recEmpty: 'Подходящих шагов сейчас нет.', complete: 'Отметить выполненным', completing: 'Обновляем прогресс…',
    hrOnly: 'Только для HR', hrError: 'Не удалось загрузить HR-данные.', weakSkills: 'Проседающие навыки', avgGap: 'средний разрыв', withoutRec: 'Без рекомендации', employees: 'сотрудников требуют внимания', privacy: 'Личная вовлечённость не раскрывается.', engagement: 'Участие в активностях',
  },
  kk: {
    path: 'Менің мансап жолым', myPath: 'Менің жолым', hr: 'HR-дашборд', light: 'Ашық тақырып', dark: 'Қараңғы тақырып', language: 'Интерфейс тілі', city: 'Алматы', address: 'Әл-Фараби даңғылы, 40',
    tenure: 'ай компанияда', selectEmployee: 'Қызметкерді таңдау', goal: 'Мақсат', noGoal: 'Келесі деңгей', trajectory: 'Келесі деңгей', radar: 'Жасыл — қазіргі деңгей, алтын жиек — қажетті деңгей.',
    skills: 'Келесі деңгейге дағдылар', critical: 'Маңызды', current: 'қазір', required: 'қажет', closeGap: 'Алшақтықты қалай жабуға болады', hoursShort: 'сағ',
    history: 'Белсенділік тарихы', historyIntro: 'Даму қадамдарыңыз және нәтижелері', noHistory: 'Әзірге белсенділік жоқ',
    recommendations: 'Ұсынылған қадамдар', recError: 'Ұсыныстарды жүктеу мүмкін болмады. Қайталап көріңіз.', recEmpty: 'Әзірге сәйкес қадамдар жоқ.', complete: 'Орындалды деп белгілеу', completing: 'Үлгерім жаңартылуда…',
    hrOnly: 'Тек HR үшін', hrError: 'HR деректерін жүктеу мүмкін болмады.', weakSkills: 'Әлсіз дағдылар', avgGap: 'орташа айырма', withoutRec: 'Ұсыныссыз', employees: 'қызметкерге назар аудару қажет', privacy: 'Жеке белсенділік көрсетілмейді.', engagement: 'Іс-шараларға қатысу',
  },
  en: {
    path: 'My career path', myPath: 'My path', hr: 'HR dashboard', light: 'Light theme', dark: 'Dark theme', language: 'Interface language', city: 'Almaty', address: '40 Al-Farabi Ave.',
    tenure: 'months with the company', selectEmployee: 'Select employee', goal: 'Goal', noGoal: 'Next grade', trajectory: 'Next level', radar: 'Green — current level, gold outline — required level.',
    skills: 'Skills for the next level', critical: 'Critical', current: 'current', required: 'required', closeGap: 'How to close the gap', hoursShort: 'h',
    history: 'Activity history', historyIntro: 'Your development steps and results', noHistory: 'No activities yet',
    recommendations: 'Recommended steps', recError: 'Could not load recommendations. Please try again.', recEmpty: 'No eligible steps right now.', complete: 'Mark as completed', completing: 'Updating progress…',
    hrOnly: 'HR only', hrError: 'Could not load HR data.', weakSkills: 'Skills with gaps', avgGap: 'average gap', withoutRec: 'Without recommendation', employees: 'employees need attention', privacy: 'Personal engagement is not shown.', engagement: 'Activity engagement',
  },
} as const

export const statusLabels: Record<Language, Record<string, string>> = {
  ru: { completed: 'Завершено', in_progress: 'В процессе', dropped: 'Прервано', no_show: 'Пропуск', declined: 'Отказ', overdue: 'Просрочено' },
  kk: { completed: 'Аяқталды', in_progress: 'Орындалуда', dropped: 'Тоқтатылды', no_show: 'Қатыспады', declined: 'Бас тартты', overdue: 'Мерзімі өтті' },
  en: { completed: 'Completed', in_progress: 'In progress', dropped: 'Dropped', no_show: 'No show', declined: 'Declined', overdue: 'Overdue' },
}

export const formatLabels: Record<Language, Record<string, string>> = {
  ru: { online: 'Онлайн', offline: 'Офлайн', self_paced: 'В своём темпе' },
  kk: { online: 'Онлайн', offline: 'Офлайн', self_paced: 'Өз қарқынымен' },
  en: { online: 'Online', offline: 'Offline', self_paced: 'Self paced' },
}