ALTER TABLE champions.moves
  ADD COLUMN target VARCHAR(16) DEFAULT 'single',
  ADD COLUMN is_spread BOOLEAN DEFAULT FALSE,
  ADD CONSTRAINT chk_move_target CHECK (
    target IN ('single', 'all_opponents', 'all_except_self', 'self')
  );
