import tkinter as tk
from tkinter import ttk, messagebox
import random
import json
from collections import defaultdict
import threading
import time

class AILearningGame:
    def __init__(self):
        self.size = 8
        self.max_moves = 100
        self.reset_game()
        self.player_data = []
        self.ai_knowledge = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'reward': 0}))
        self.training_games = 0
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("AI Learning Game")
        self.root.geometry("800x600")
        self.root.configure(bg='#2C3E50')
        
        self.setup_gui()
        
    def reset_game(self):
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.player_pos = [0, 0]
        self.ai_pos = [self.size-1, self.size-1]
        self.player_score = 0
        self.ai_score = 0
        self.game_over = False
        self.moves = 0
        self.items_remaining = 0
        self.place_items()
        
    def place_items(self):
        # Items: gold=3, silver=2, trap=-1, obstacle=-2
        items = [(3, 3), (2, 5), (-1, 4), (-2, 6)]  # (value, count)
        self.items_remaining = 8  # 3 gold + 5 silver
        
        for value, count in items:
            for _ in range(count):
                pos = self.get_random_empty()
                if pos:
                    self.board[pos[0]][pos[1]] = value
                    
        self.board[self.player_pos[0]][self.player_pos[1]] = 10  # Player
        self.board[self.ai_pos[0]][self.ai_pos[1]] = 20  # AI
        
    def get_random_empty(self):
        for _ in range(50):
            x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if (self.board[x][y] == 0 and 
                [x, y] != self.player_pos and 
                [x, y] != self.ai_pos):
                return [x, y]
        return None
        
    def move(self, direction, is_player=True):
        if self.game_over:
            return False
            
        pos = self.player_pos if is_player else self.ai_pos
        new_pos = pos.copy()
        
        moves = {'up': [-1, 0], 'down': [1, 0], 'left': [0, -1], 'right': [0, 1]}
        if direction in moves:
            new_pos[0] += moves[direction][0]
            new_pos[1] += moves[direction][1]
        else:
            return False
            
        # Check bounds and obstacles
        if (new_pos[0] < 0 or new_pos[0] >= self.size or 
            new_pos[1] < 0 or new_pos[1] >= self.size or
            self.board[new_pos[0]][new_pos[1]] == -2):
            return False
            
        # Clear old position
        self.board[pos[0]][pos[1]] = 0
        
        # Handle rewards
        reward = 0
        cell_value = self.board[new_pos[0]][new_pos[1]]
        
        if cell_value == 3:  # Gold
            reward = 5
            self.items_remaining -= 1
        elif cell_value == 2:  # Silver
            reward = 3
            self.items_remaining -= 1
        elif cell_value == -1:  # Trap
            reward = -2
            
        # Update position and score
        if is_player:
            self.player_pos = new_pos
            self.player_score += reward
            self.board[new_pos[0]][new_pos[1]] = 10
            self.record_player_move(direction, reward)
        else:
            self.ai_pos = new_pos
            self.ai_score += reward
            self.board[new_pos[0]][new_pos[1]] = 20
            
        self.moves += 1
        
        # Check game end
        if self.items_remaining <= 0 or self.moves >= self.max_moves:
            self.game_over = True
            
        return True
        
    def record_player_move(self, direction, reward):
        state = self.get_game_state()
        self.player_data.append({
            'position': self.player_pos.copy(),
            'action': direction,
            'reward': reward,
            'state': state
        })
        
    def get_game_state(self):
        return {
            'player_pos': self.player_pos.copy(),
            'ai_pos': self.ai_pos.copy(),
            'nearby_rewards': len(self.get_nearby_rewards()),
            'player_score': self.player_score,
            'ai_score': self.ai_score
        }
        
    def get_nearby_rewards(self):
        rewards = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                x, y = self.player_pos[0] + dx, self.player_pos[1] + dy
                if (0 <= x < self.size and 0 <= y < self.size and 
                    0 < self.board[x][y] < 10):
                    rewards.append([x, y, self.board[x][y]])
        return rewards
        
    def get_valid_moves(self, pos):
        moves = []
        directions = {'up': [-1, 0], 'down': [1, 0], 'left': [0, -1], 'right': [0, 1]}
        
        for direction, (dx, dy) in directions.items():
            new_x, new_y = pos[0] + dx, pos[1] + dy
            if (0 <= new_x < self.size and 0 <= new_y < self.size and
                self.board[new_x][new_y] != -2):
                moves.append(direction)
        return moves
        
    def make_ai_move(self):
        if self.game_over:
            return
            
        valid_moves = self.get_valid_moves(self.ai_pos)
        if not valid_moves:
            return
            
        if self.training_games < 5:
            # Random exploration
            move = random.choice(valid_moves)
        else:
            # Strategic move
            move = self.choose_best_ai_move(valid_moves)
            
        success = self.move(move, False)
        if success:
            self.update_ai_knowledge(move)
            
    def choose_best_ai_move(self, valid_moves):
        best_move = valid_moves[0]
        best_score = float('-inf')
        
        for move in valid_moves:
            score = self.evaluate_move(move)
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
        
    def evaluate_move(self, direction):
        moves = {'up': [-1, 0], 'down': [1, 0], 'left': [0, -1], 'right': [0, 1]}
        dx, dy = moves[direction]
        new_pos = [self.ai_pos[0] + dx, self.ai_pos[1] + dy]
        
        score = 0
        cell_value = self.board[new_pos[0]][new_pos[1]]
        
        # Direct rewards
        if cell_value == 3:
            score += 10  # Gold
        elif cell_value == 2:
            score += 6   # Silver
        elif cell_value == -1:
            score -= 5   # Trap
            
        # Nearby rewards bonus
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                x, y = new_pos[0] + dx, new_pos[1] + dy
                if 0 <= x < self.size and 0 <= y < self.size:
                    if self.board[x][y] == 3:
                        score += 3
                    elif self.board[x][y] == 2:
                        score += 1
                        
        return score
        
    def update_ai_knowledge(self, move):
        state_key = f"{self.ai_pos[0]},{self.ai_pos[1]},{len(self.get_nearby_rewards())}"
        reward = 1 if self.ai_score > self.player_score else -1
        
        self.ai_knowledge[state_key][move]['count'] += 1
        self.ai_knowledge[state_key][move]['reward'] += reward
        
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2C3E50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = tk.Label(main_frame, text="🎮 AI Learning Game", 
                        font=('Arial', 20, 'bold'), fg='white', bg='#2C3E50')
        title.pack(pady=10)
        
        # Stats frame
        stats_frame = tk.Frame(main_frame, bg='#34495E')
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.player_score_label = tk.Label(stats_frame, text="Player: 0", 
                                          font=('Arial', 12), fg='white', bg='#34495E')
        self.player_score_label.pack(side=tk.LEFT, padx=10)
        
        self.ai_score_label = tk.Label(stats_frame, text="AI: 0", 
                                      font=('Arial', 12), fg='white', bg='#34495E')
        self.ai_score_label.pack(side=tk.LEFT, padx=10)
        
        self.games_label = tk.Label(stats_frame, text="Games: 0", 
                                   font=('Arial', 12), fg='white', bg='#34495E')
        self.games_label.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(stats_frame, text="Moves: 0/100", 
                                    font=('Arial', 12), fg='white', bg='#34495E')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Board frame
        board_frame = tk.Frame(main_frame, bg='#2C3E50')
        board_frame.pack(pady=10)
        
        self.cells = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                cell = tk.Label(board_frame, width=4, height=2, 
                               font=('Arial', 12, 'bold'), 
                               relief=tk.RAISED, borderwidth=2)
                cell.grid(row=i, column=j, padx=1, pady=1)
                row.append(cell)
            self.cells.append(row)
            
        # Controls frame
        controls_frame = tk.Frame(main_frame, bg='#2C3E50')
        controls_frame.pack(pady=10)
        
        # Movement buttons
        move_frame = tk.Frame(controls_frame, bg='#2C3E50')
        move_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Button(move_frame, text="↑", command=lambda: self.player_move('up'),
                 font=('Arial', 14), width=3).grid(row=0, column=1)
        tk.Button(move_frame, text="←", command=lambda: self.player_move('left'),
                 font=('Arial', 14), width=3).grid(row=1, column=0)
        tk.Button(move_frame, text="→", command=lambda: self.player_move('right'),
                 font=('Arial', 14), width=3).grid(row=1, column=2)
        tk.Button(move_frame, text="↓", command=lambda: self.player_move('down'),
                 font=('Arial', 14), width=3).grid(row=2, column=1)
        
        # Game buttons
        button_frame = tk.Frame(controls_frame, bg='#2C3E50')
        button_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Button(button_frame, text="New Game", command=self.new_game,
                 font=('Arial', 10), bg='#3498DB', fg='white').pack(pady=2)
        tk.Button(button_frame, text="Train AI", command=self.train_ai,
                 font=('Arial', 10), bg='#E74C3C', fg='white').pack(pady=2)
        tk.Button(button_frame, text="Auto Play", command=self.auto_play,
                 font=('Arial', 10), bg='#F39C12', fg='white').pack(pady=2)
        
        # Log
        log_frame = tk.Frame(main_frame, bg='#2C3E50')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, bg='#1C2833', fg='white',
                               font=('Courier', 9))
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_display()
        self.log("Welcome to AI Learning Game!")
        self.log("Use arrow buttons to move. Collect G(old) and S(ilver), avoid T(raps)!")
        
    def update_display(self):
        colors = {
            0: ('#F8F9FA', ''),      # Empty
            10: ('#28A745', 'P'),    # Player
            20: ('#DC3545', 'AI'),   # AI
            3: ('#FFD700', 'G'),     # Gold
            2: ('#C0C0C0', 'S'),     # Silver
            -1: ('#8B0000', 'T'),    # Trap
            -2: ('#343A40', '■')     # Obstacle
        }
        
        for i in range(self.size):
            for j in range(self.size):
                value = self.board[i][j]
                bg_color, text = colors.get(value, ('#F8F9FA', ''))
                
                self.cells[i][j].configure(bg=bg_color, text=text,
                                          fg='white' if value in [10, 20, -1, -2] else 'black')
                
        # Update stats
        self.player_score_label.configure(text=f"Player: {self.player_score}")
        self.ai_score_label.configure(text=f"AI: {self.ai_score}")
        self.games_label.configure(text=f"Games: {self.training_games}")
        self.status_label.configure(text=f"Moves: {self.moves}/{self.max_moves} | Items: {self.items_remaining}")
        
        if self.game_over:
            winner = "Player" if self.player_score > self.ai_score else "AI" if self.ai_score > self.player_score else "Tie"
            messagebox.showinfo("Game Over", f"Winner: {winner}\nPlayer: {self.player_score}, AI: {self.ai_score}")
            
    def player_move(self, direction):
        if self.move(direction, True):
            self.log(f"Player moved {direction} (Score: {self.player_score})")
            self.update_display()
            
            if not self.game_over:
                self.root.after(500, self.delayed_ai_move)
                
    def delayed_ai_move(self):
        self.make_ai_move()
        self.log(f"AI moved (Score: {self.ai_score})")
        self.update_display()
        
    def new_game(self):
        self.reset_game()
        self.update_display()
        self.log("New game started!")
        
    def train_ai(self):
        self.log("Training AI...")
        
        def training_thread():
            for i in range(10):
                self.reset_game()
                
                while not self.game_over and self.moves < self.max_moves:
                    # Random player move
                    player_moves = self.get_valid_moves(self.player_pos)
                    if player_moves:
                        self.move(random.choice(player_moves), True)
                        
                    # AI move
                    if not self.game_over:
                        self.make_ai_move()
                        
                self.training_games += 1
                self.root.after(0, lambda i=i: self.log(f"Training {i+1}: P{self.player_score}, AI{self.ai_score}"))
                
            self.root.after(0, self.finish_training)
            
        threading.Thread(target=training_thread, daemon=True).start()
        
    def finish_training(self):
        self.reset_game()
        self.update_display()
        self.log("Training complete! AI is smarter now.")
        
    def auto_play(self):
        if self.game_over:
            return
            
        player_moves = self.get_valid_moves(self.player_pos)
        if player_moves:
            self.move(random.choice(player_moves), True)
            self.update_display()
            
            if not self.game_over:
                self.root.after(500, lambda: (self.make_ai_move(), self.update_display()))
                self.root.after(1500, self.auto_play)
                
    def log(self, message):
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = AILearningGame()
    game.run()
