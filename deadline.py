"""""This module allows you to more easily use the ``CG_INFO`` feature of
CodeGrade and deduct points from students for days past the deadline.
"""""
import os as _os
import json as _json
import dataclasses
from typing import Any as _Any
from typing import Optional as _Optional
from datetime import datetime as _datetime
from datetime import timedelta, timezone
import math

__all__ = ('CG_INFO', )

@dataclasses.dataclass
class _CGInfo:
    submission_id: _Optional[int]
    student_id: _Optional[int]
    submitted_at: _Optional[_datetime]
    deadline: _Optional[_datetime]
    lock_date: _Optional[_datetime]

    @classmethod
    def _load(cls) -> '_CGInfo':
        # pylint: disable=import-outside-toplevel

        def _maybe_datetime(value: _Optional[str]) -> _Optional[_datetime]:
            if value is None:
                return None
            try:
                return _datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return None

        def _to_int(value: _Any) -> _Optional[int]:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        try:
            unparsed_cg_info = _json.loads(_os.getenv('CG_INFO', '{}'))
        except ValueError as ex:
            print(ex)
            unparsed_cg_info = {}

        return cls(
            submission_id=_to_int(unparsed_cg_info.get('submission_id')),
            student_id=_to_int(unparsed_cg_info.get('student_id')),
            submitted_at=_maybe_datetime(unparsed_cg_info.get('submitted_at')),
            deadline=_maybe_datetime(unparsed_cg_info.get('deadline')),
            lock_date=_maybe_datetime(unparsed_cg_info.get('lock_date')),
        )


CG_INFO = _CGInfo._load()

ONE_DAY      = timedelta(days=1)
ONE_HOUR = timedelta(hours=1)
deadline     = CG_INFO.deadline
deadline = _datetime.fromisoformat('2024-11-03T21:00:00-04:00')
submitted_at = CG_INFO.submitted_at
#print('deadline:', deadline)
#print('submitted_at:', submitted_at)
hours_late = max(0, int(math.floor((submitted_at - deadline) / ONE_HOUR)))

max_hours_late = 50
max_points = 100
deduction = -max_points * min(hours_late / max_hours_late, 1)


print('Hours Late:', hours_late)
print('Points Deducted:', abs(deduction))
points = str(1 - min(hours_late / max_hours_late, 1))

with open(3, "w") as f:
    result = { "tag": "points", "points": points}
    f.write(_json.dumps(result))