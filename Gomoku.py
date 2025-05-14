import math
import random
import tkinter as tk
from tkinter import ttk
import pygame  
import numpy as np
##################################### Game #####################################
class Gomoku:
    def __init__(self, size = 15):
        self.size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]

    def print_board(self):
        print("   ", end="")
        for col in range(self.size):
            print(f"{col:2}", end=" ")
        print()
        for row in range(self.size):
            print(f"{row:2}  ", end="")
            for col in range(self.size):
                cell = self.board[row][col]
                symbol = "." if cell == 0 else ("X" if cell == 1 else "O")
                print(f"{symbol:2}", end=" ")
            print()

    def is_valid_move(self, row, col):
        return (
            0 <= row < self.size and
            0 <= col < self.size and
            self.board[row][col] == 0
        )

    def make_move(self, row, col, player):
        if self.is_valid_move(row, col):
            self.board[row][col] = player
            return True
        return False

    def undo_move(self, row, col):
        if 0 <= row < self.size and 0 <= col < self.size:
            self.board[row][col] = 0

    def get_legal_moves(self):
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == 0]

    def check_win(self, player):
        def count_consecutive(r_step, c_step, row, col):
            count = 0
            while (0 <= row < self.size and 0 <= col < self.size and self.board[row][col] == player):
                count += 1
                row += r_step
                col += c_step
            return count

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != player:
                    continue
                if (
                    count_consecutive(0, 1, row, col) >= 5 or
                    count_consecutive(1, 0, row, col) >= 5 or
                    count_consecutive(1, 1, row, col) >= 5 or
                    count_consecutive(1, -1, row, col) >= 5
                ):
                    return True
        return False

    def is_draw(self):
        return all(cell != 0 for row in self.board for cell in row)
################################### get line ###################################
def get_lines(board):
        size = len(board)
        lines = []

        # Rows
        for row in board:
            lines.append(row)

        # Columns
        for c in range(size):
            lines.append([board[r][c] for r in range(size)])

        # Diagonals top left => bottom down
        for r in range(size):
            diag = []
            i, j = r, 0
            while i < size and j < size:
                diag.append(board[i][j])
                i += 1
                j += 1
            if len(diag) >= 5:
                lines.append(diag)

        for c in range(1, size):
            diag = []
            i, j = 0, c
            while i < size and j < size:
                diag.append(board[i][j])
                i += 1
                j += 1
            if len(diag) >= 5:
                lines.append(diag)

        # Diagonals top right => bottom left
        for r in range(size):
            diag = []
            i, j = r, size - 1
            while i < size and j >= 0:
                diag.append(board[i][j])
                i += 1
                j -= 1
            if len(diag) >= 5:
                lines.append(diag)

        for c in range(size - 2, -1, -1):
            diag = []
            i, j = 0, c
            while i < size and j >= 0:
                diag.append(board[i][j])
                i += 1
                j -= 1
            if len(diag) >= 5:
                lines.append(diag)

        return lines
#################################### Score #####################################
def evaluate_line(line, player):
        s = ''.join(str(cell) for cell in line)
        opponent = '2' if player == 1 else '1'
        me = str(player)
        score = 0

        patterns = {
            f"{me*5}": 1000000,
            f"0{me*4}0": 100000,
            f"{opponent}{me*4}0": 10000,
            f"0{me*4}{opponent}": 10000,
            f"0{me*3}00": 10000,
            f"00{me*3}0": 10000,
            f"0{me*3}0": 10000,
            f"0{me}{me}0{me}0": 8000,
            f"0{me}0{me}{me}0": 8000,
            f"{opponent}{me*3}0": 5000,
            f"0{me*3}{opponent}": 5000,
            f"0{me*2}00": 2000,
            f"00{me*2}0": 2000,
            f"0{me*2}0": 2000,
            f"0{me}0{me}00": 2000,
            f"00{me}0{me}0": 2000,
            f"0{me}00{me}0": 2000,
            f"0{me}0": 1000,
        }

        for pattern, value in patterns.items():
            count = s.count(pattern)
            if count:
                score += count * value

        return score
################################# Score_board ##################################
def evaluate_board(board, player):
    opponent = 2 if player == 1 else 1

    score = 0
    for line in get_lines(board):
        score += evaluate_line(line, player)
        score -= evaluate_line(line, opponent)

    return score
#################################### opening ####################################
def generate_opening_book(board_size):
    center = board_size // 2
    opening = [
        (center, center),
        (center, center - 1),          
        (center, center + 1),       
        (center - 1, center),      
        (center + 1, center),
    ]
    return [move for move in opening if 0 <= move[0] < board_size and 0 <= move[1] < board_size]
#################################### player ####################################
class Player:
    def __init__(self, player_id, name):
        self.player_id = player_id
        self.name = name

    def get_move(self, game):
        raise NotImplementedError("This method should be implemented by subclasses.")
##################################### Human ####################################
class HumanPlayer(Player):
    def get_move(self, game):
        while True:
            try:
                row = int(input(f"{self.name} (Player {self.player_id}) row: "))
                col = int(input(f"{self.name} (Player {self.player_id}) col: "))
                if game.is_valid_move(row, col):
                    return row, col
                else:
                    print("Invalid move. Cell is occupied or out of bounds.")
            except ValueError:
                print("Please enter numeric values.")
#################################### Min-Max ###################################
class MinimaxAIPlayer(Player):
    def __init__(self, player_id, name, depth = 2):
        super().__init__(player_id, name)
        self.max_depth = depth

    def get_move(self, game):
        legal_moves = game.get_legal_moves()
        opening = generate_opening_book(game.size)

        move_num = game.size * game.size - len(legal_moves)
        if move_num < len(opening):
            valid_opening_moves = [move for move in opening if game.is_valid_move(*move)]
            if valid_opening_moves:
                move = random.choice(valid_opening_moves)
                return move

        best_score = -math.inf
        best_moves = []
        for move in game.get_legal_moves():
            row, col = move
            game.make_move(row, col, self.player_id)
            score = self.minimax(game, depth=self.max_depth - 1, maximizing = False)
            game.undo_move(row, col)

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        best = random.choice(best_moves)
        rowi , coli = best
        print(f"player: {self.name} played at row: {rowi}, col: {coli}.")
        return best if best_moves else random.choice(game.get_legal_moves())

    def minimax(self, game, depth, maximizing):
        current_player = self.player_id if maximizing else (2 if self.player_id == 1 else 1)

        if game.check_win(self.player_id):
            return 1e6 + depth  
        if game.check_win(2 if self.player_id == 1 else 1):
            return -1e6 - depth  
        if game.is_draw() or depth == 0:
            return evaluate_board(game.board, self.player_id)

        legal_moves = game.get_legal_moves()
        if maximizing:
            max_eval = -math.inf
            for move in legal_moves:
                game.make_move(move[0], move[1], current_player)
                eval = self.minimax(game, depth - 1, False)
                game.undo_move(move[0], move[1])
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = math.inf
            for move in legal_moves:
                game.make_move(move[0], move[1], current_player)
                eval = self.minimax(game, depth - 1, True)
                game.undo_move(move[0], move[1])
                min_eval = min(min_eval, eval)
            return min_eval
################################### Alpha-Beta #################################
class AlphaBetaAIPlayer(Player):
    def __init__(self, player_id, name, depth = 2):
        super().__init__(player_id, name)
        self.max_depth = depth

    def get_move(self, game):
        legal_moves = game.get_legal_moves()
        opening = generate_opening_book(game.size)

        move_num = game.size * game.size - len(legal_moves)
        if move_num < len(opening):
            valid_opening_moves = [move for move in opening if game.is_valid_move(*move)]
            if valid_opening_moves:
                move = random.choice(valid_opening_moves)
                return move

        best_score = -math.inf
        best_moves = []
        alpha = -math.inf
        beta = math.inf

        for move in game.get_legal_moves():
            row, col = move
            game.make_move(row, col, self.player_id)
            score = self.alphabeta(game, depth=self.max_depth - 1, alpha=alpha, beta=beta, maximizing=False)
            game.undo_move(row, col)

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        best = random.choice(best_moves)
        rowi , coli = best
        print(f"Player: {self.name} played at row: {rowi}, col: {coli}")
        return best if best_moves else random.choice(game.get_legal_moves())

    def alphabeta(self, game, depth, alpha, beta, maximizing):
        current_player = self.player_id if maximizing else (2 if self.player_id == 1 else 1)

        if game.check_win(self.player_id):
            return 1e6 + depth
        if game.check_win(2 if self.player_id == 1 else 1):
            return -1e6 - depth
        if game.is_draw() or depth == 0:
            return evaluate_board(game.board, self.player_id)

        legal_moves = game.get_legal_moves()
        if maximizing:
            value = -math.inf
            for move in legal_moves:
                game.make_move(move[0], move[1], current_player)
                value = max(value, self.alphabeta(game, depth - 1, alpha, beta, False))
                game.undo_move(move[0], move[1])
                alpha = max(alpha, value)
                if alpha >= beta:
                    break 
            return value
        else:
            value = math.inf
            for move in legal_moves:
                game.make_move(move[0], move[1], current_player)
                value = min(value, self.alphabeta(game, depth - 1, alpha, beta, True))
                game.undo_move(move[0], move[1])
                beta = min(beta, value)
                if beta <= alpha:
                    break 
            return value
#################################### Type #####################################
def choose_player(player_id):
    print(f"\nSelect type for Player {player_id}:")
    print("1. Human")
    print("2. Minimax AI")
    print("3. Alpha-Beta AI")
    while True:
        try:
            choice = int(input("Enter your choice (1-3): "))
            if choice in [1, 2, 3]:
                name = input(f"Enter name for Player {player_id}: ")
                if choice == 1:
                    return HumanPlayer(player_id, name)
                elif choice == 2:
                    return MinimaxAIPlayer(player_id, name)
                else:
                    return AlphaBetaAIPlayer(player_id, name)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a number.")
##################################### GUI ######################################
class GomokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gomoku Game")
        self.root.geometry("900x700")
        pygame.mixer.init()
        self.load_sounds()
        self.setup_styles()
        self.show_setup_page()
        self.last_move = None

    def load_sounds(self):
        try:
            self.click_sound = pygame.mixer.Sound(buffer=self.generate_beep(200, 0.1))
            self.win_sound = pygame.mixer.Sound(buffer=self.generate_beep(400, 0.4))
        except:
            self.click_sound = None
            self.win_sound = None

    def generate_beep(self, frequency, duration):
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sin(2 * np.pi * frequency * t)
        return (wave * 32767).astype(np.int16).tobytes()

    def setup_styles(self):
        self.colors = {
            'primary': '#8B4513',       
            'secondary': '#D2B48C',     
            'accent': '#A0522D',        
            'light': '#F5DEB3',         
            'dark': '#5D4037',          
            'text': '#FFFFFF',          
            'text_dark': '#000000',     
            'highlight': '#CD853F',     
            'board': '#E6C88C',        
            'win_highlight': '#4CAF50',
            'last_move': '#F22'
        }

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.colors['light'])
        style.configure('TLabel', background=self.colors['light'], foreground=self.colors['dark'], font=('Helvetica', 12))
        style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'), foreground=self.colors['primary'])
        style.configure('Subtitle.TLabel', font=('Helvetica', 16), foreground=self.colors['accent'])
        style.configure('Result.TLabel', font=('Helvetica', 18, 'bold'), foreground=self.colors['win_highlight'])
        style.configure('TButton', font=('Helvetica', 12), padding=8)
        style.configure('Game.TButton', font=('Helvetica', 12, 'bold'), background=self.colors['primary'], foreground=self.colors['text'], padding=10)
        style.map('Game.TButton', background=[('active', self.colors['accent']), ('!disabled', self.colors['primary'])], 
        foreground=[('active', self.colors['text']), ('!disabled', self.colors['text'])])

    def show_setup_page(self):
        self.clear_window()
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH,expand=True)
        
        title = ttk.Label(main_frame, text="Gomoku Game Setup", style='Title.TLabel')
        title.pack(pady=(20,0)) 
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, padx=50)  
        
        # Board size
        ttk.Label(form_frame, text="Board Size (5-19):").grid(row=0, column=0, sticky=tk.W, pady=(40,0))
        self.board_size = tk.IntVar(value=9)
        size_entry = ttk.Entry(form_frame, textvariable=self.board_size, width=5, style='TEntry')
        size_entry.grid(row=0, column=1, sticky=tk.W, pady=(50,0))
        
        # Player 1 setup
        ttk.Label(form_frame, text="Player 1 (White):", style='Subtitle.TLabel').grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(30,0))
        
        ttk.Label(form_frame, text="Name:").grid(row=2, column=0, sticky=tk.W, pady=7)
        self.p1_name = tk.StringVar(value="mini")
        p1_name_entry = ttk.Entry(form_frame, textvariable=self.p1_name, style='TEntry')
        p1_name_entry.grid(row=2, column=1, sticky=tk.W, pady=7)
        
        ttk.Label(form_frame, text="Type:").grid(row=3, column=0, sticky=tk.W, pady=7)
        self.p1_type = tk.StringVar(value="Human")
        p1_type_menu = ttk.OptionMenu(form_frame, self.p1_type, "Minimax AI", "Human", "Minimax AI", "Alpha-Beta AI")
        p1_type_menu.grid(row=3, column=1, sticky=tk.W, pady=7)
        
        ttk.Label(form_frame, text="AI Depth (if applicable):").grid(row=4, column=0, sticky=tk.W, pady=7)
        self.p1_depth = tk.IntVar(value=2)
        p1_depth_entry = ttk.Entry(form_frame, textvariable=self.p1_depth, width=5, style='TEntry')
        p1_depth_entry.grid(row=4, column=1, sticky=tk.W, pady=7)
        
        # Player 2 setup 
        ttk.Label(form_frame, text="Player 2 (Black):", style='Subtitle.TLabel').grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(70,0))
        
        ttk.Label(form_frame, text="Name:").grid(row=6, column=0, sticky=tk.W, pady=7)
        self.p2_name = tk.StringVar(value="alpha")
        p2_name_entry = ttk.Entry(form_frame, textvariable=self.p2_name, style='TEntry')
        p2_name_entry.grid(row=6, column=1, sticky=tk.W, pady=7)
        
        ttk.Label(form_frame, text="Type:").grid(row=7, column=0, sticky=tk.W, pady=7)
        self.p2_type = tk.StringVar(value="Human")
        p2_type_menu = ttk.OptionMenu(form_frame, self.p2_type, "Alpha-Beta AI", "Human", "Minimax AI", "Alpha-Beta AI")
        p2_type_menu.grid(row=7, column=1, sticky=tk.W, pady=7)
        
        ttk.Label(form_frame, text="AI Depth (if applicable):").grid(row=8, column=0, sticky=tk.W, pady=7)
        self.p2_depth = tk.IntVar(value=2)
        p2_depth_entry = ttk.Entry(form_frame, textvariable=self.p2_depth, width=5, style='TEntry')
        p2_depth_entry.grid(row=8, column=1, sticky=tk.W, pady=7)
        
        # Start button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        start_button = ttk.Button(button_frame, text="Start Game", style='Game.TButton', command=self.start_game)
        start_button.pack(pady=(105,30))
        
        self.p1_type.trace_add('write', lambda *args: self.toggle_depth_field(p1_depth_entry, self.p1_type))
        self.p2_type.trace_add('write', lambda *args: self.toggle_depth_field(p2_depth_entry, self.p2_type))
        self.toggle_depth_field(p1_depth_entry, self.p1_type)
        self.toggle_depth_field(p2_depth_entry, self.p2_type)
        
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=3)
    
    def toggle_depth_field(self, field, type_var):
        if type_var.get() == "Human":
            field.grid_remove()
        else:
            field.grid()
    
    def start_game(self):
        size = self.board_size.get()
        if size < 5 or size > 19:
            raise ValueError("Board size must be between 5 and 19")

        self.game = Gomoku(size)
        self.players = [
            self.create_player(1, self.p1_name.get(), self.p1_type.get(), self.p1_depth.get()),
            self.create_player(2, self.p2_name.get(), self.p2_type.get(), self.p2_depth.get())
        ]
        self.current_player = 0
        self.game_over = False
        self.game_result = ""
        self.show_game_board()

    def create_player(self, player_id, name, player_type, depth):
        if player_type == "Human":
            return HumanPlayer(player_id, name)
        elif player_type == "Minimax AI":
            return MinimaxAIPlayer(player_id, name, depth)
        elif player_type == "Alpha-Beta AI":
            return AlphaBetaAIPlayer(player_id, name, depth)
    
    def show_game_board(self):
        self.clear_window()
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Game status frame
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        self.update_status_display()
        
        # Game info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Player 1 info
        p1_frame = ttk.Frame(info_frame)
        p1_frame.pack(side=tk.LEFT, expand=True)
        ttk.Label(p1_frame, text=f"{self.players[0].name} (White)", style='Subtitle.TLabel').pack()
        ttk.Label(p1_frame, text=f"Type: {self.p1_type.get()}").pack()
        if self.p1_type.get() != "Human":
            ttk.Label(p1_frame, text=f"Depth: {self.p1_depth.get()}").pack()
        
        # Player 2 info
        p2_frame = ttk.Frame(info_frame)
        p2_frame.pack(side=tk.LEFT, expand=True)
        ttk.Label(p2_frame, text=f"{self.players[1].name} (Black)", style='Subtitle.TLabel').pack()
        ttk.Label(p2_frame, text=f"Type: {self.p2_type.get()}").pack()
        if self.p2_type.get() != "Human":
            ttk.Label(p2_frame, text=f"Depth: {self.p2_depth.get()}").pack()
        
        # Game board frame
        board_frame = ttk.Frame(main_frame)
        board_frame.pack(expand=True, fill=tk.BOTH, pady=10)
        
        self.canvas = tk.Canvas(board_frame, bg=self.colors['board'], highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        
        # Control buttons frame - centered
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Center the buttons using another frame
        center_frame = ttk.Frame(button_frame)
        center_frame.pack()
        
        # Play Again button
        play_again_button = ttk.Button(center_frame, text="Play Again", style='Game.TButton', command=self.reset_game)
        play_again_button.pack(side=tk.LEFT, padx=60)
        
        # Back to Setup button
        reset_button = ttk.Button(center_frame, text="Back to Setup", style='Game.TButton', command=self.show_setup_page)
        reset_button.pack(side=tk.LEFT, padx=60)
        
        # Force window update and draw board
        self.root.update_idletasks()
        self.draw_board()
        
        # Start the game
        if not self.game_over:
            if isinstance(self.players[self.current_player], HumanPlayer):
                self.canvas.bind("<Button-1>", self.handle_click)
            else:
                self.root.after(100, self.ai_move)
    
    def update_status_display(self):
        for widget in self.status_frame.winfo_children():
            widget.destroy()
        
        if self.game_over:
            result_label = ttk.Label(self.status_frame, text=self.game_result, style='Result.TLabel')
            result_label.pack()
        else:
            turn_label = ttk.Label(self.status_frame, text=f"Current Turn: {self.players[self.current_player].name}", style='Subtitle.TLabel')
            turn_label.pack()

    def draw_board(self):
        self.canvas.delete("all")
        size = self.game.size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        cell_size = min(canvas_width, canvas_height) / (size + 1)
        
        x_offset = (canvas_width - size * cell_size) / 2
        y_offset = (canvas_height - size * cell_size) / 2
        
        for i in range(size + 1):
            self.canvas.create_line(
                x_offset, y_offset + i * cell_size,
                x_offset + size * cell_size, y_offset + i * cell_size,
                fill=self.colors['dark'], width=2
            )
            self.canvas.create_line(
                x_offset + i * cell_size, y_offset,
                x_offset + i * cell_size, y_offset + size * cell_size,
                fill=self.colors['dark'], width=2
            )
        
        for row in range(size):
            for col in range(size):
                if self.game.board[row][col] == 1: 
                    self.draw_piece(col, row, "white", cell_size, x_offset, y_offset)
                elif self.game.board[row][col] == 2: 
                    self.draw_piece(col, row, "black", cell_size, x_offset, y_offset)
        
        if self.last_move:
            last_row, last_col = self.last_move
            x = x_offset + (last_col + 0.5) * cell_size
            y = y_offset + (last_row + 0.5) * cell_size
            radius = cell_size * 0.4
            
            self.canvas.create_oval(
                x - radius - 3, y - radius - 3,
                x + radius + 3, y + radius + 3,
                outline=self.colors['last_move'], width=3
            )
        
        if size >= 13:
            star_points = [
                (3, 3), (size//2, 3), (size-4, 3),
                (3, size//2), (size//2, size//2), (size-4, size//2),
                (3, size-4), (size//2, size-4), (size-4, size-4)
            ]
            
            for col, row in star_points:
                x = x_offset + col * cell_size
                y = y_offset + row * cell_size
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=self.colors['dark'], outline="")

    def draw_piece(self, col, row, color, cell_size, x_offset, y_offset):
        x = x_offset + (col + 0.5) * cell_size
        y = y_offset + (row + 0.5) * cell_size
        radius = cell_size * 0.4
        
        if color == "white":
            shadow_offset = 1
            shadow_color = "#AAAAAA"
        else:
            shadow_offset = 2
            shadow_color = "#333333"
        
        self.canvas.create_oval(
            x - radius + shadow_offset, y - radius + shadow_offset,
            x + radius + shadow_offset, y + radius + shadow_offset,
            fill=shadow_color, outline=""
        )
        
        self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color, outline=self.colors['dark'], width=1
        )
    
    def handle_click(self, event):
        if not isinstance(self.players[self.current_player], HumanPlayer):
            return
        
        size = self.game.size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        cell_size = min(canvas_width, canvas_height) / (size + 1)
        x_offset = (canvas_width - size * cell_size) / 2
        y_offset = (canvas_height - size * cell_size) / 2
        
        col = int((event.x - x_offset) // cell_size)
        row = int((event.y - y_offset) // cell_size)
        
        if 0 <= row < size and 0 <= col < size:
            self.make_move(row, col)

    def make_move(self, row, col):
        if self.click_sound:
            self.click_sound.play()
            
        player = self.players[self.current_player]
        
        if self.game.make_move(row, col, player.player_id):
            self.last_move = (row, col)
            self.draw_board()
            
            if self.game.check_win(player.player_id):
                if self.win_sound:
                    self.win_sound.play()
                self.show_result(f"{player.name} wins!")
                return
            elif self.game.is_draw():
                self.show_result("The game is a draw!")
                return
            
            self.current_player = 1 - self.current_player
            self.update_status_display()
            
            if not self.game_over and not isinstance(self.players[self.current_player], HumanPlayer):
                self.root.after(100, self.ai_move)
    
    def show_result(self, message):
        self.game_over = True
        self.game_result = message
        self.update_status_display()
        
        if "wins" in message:
            self.highlight_winning_pieces()
        
        self.canvas.unbind("<Button-1>")

    def reset_game(self):
        size = self.board_size.get()
        self.game = Gomoku(size)
        self.current_player = 0
        self.game_over = False
        self.game_result = ""
        self.last_move = None
        
        self.update_status_display()
        self.draw_board()
        
        if isinstance(self.players[self.current_player], HumanPlayer):
            self.canvas.bind("<Button-1>", self.handle_click)
        else:
            self.root.after(100, self.ai_move)

    def highlight_winning_pieces(self):
        size = self.game.size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        cell_size = min(canvas_width, canvas_height) / (size + 1)
        x_offset = (canvas_width - size * cell_size) / 2
        y_offset = (canvas_height - size * cell_size) / 2
        
        winning_player = 1 if "Player 1" in self.game_result or self.players[0].name in self.game_result else 2
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        winning_sequence = []
        for row in range(size):
            for col in range(size):
                if self.game.board[row][col] == winning_player:
                    for dr, dc in directions:
                        sequence = []
                        for i in range(5):
                            r, c = row + i*dr, col + i*dc
                            if 0 <= r < size and 0 <= c < size and self.game.board[r][c] == winning_player:
                                sequence.append((r, c))
                            else:
                                break
                        if len(sequence) >= 5:
                            winning_sequence = sequence[:5]
                            break
                    if winning_sequence:
                        break
                if winning_sequence:
                    break
        
        for row, col in winning_sequence:
            x = x_offset + (col + 0.5) * cell_size
            y = y_offset + (row + 0.5) * cell_size
            radius = cell_size * 0.4
            
            self.canvas.create_oval(
                x - radius - 3, y - radius - 3,
                x + radius + 3, y + radius + 3,
                outline=self.colors['win_highlight'], width=3
            )
    
    def ai_move(self):
        if not self.game_over:
            player = self.players[self.current_player]
            row, col = player.get_move(self.game)
            self.make_move(row, col)
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
##################################### main #####################################
# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = GomokuGUI(root)
    root.mainloop()

# Run the application
# if __name__ == "__main__":
#     game = Gomoku(9)
#     print("Welcome to Gomoku!")

#     player1 = choose_player(1)
#     player2 = choose_player(2)
#     current_player = player1

#     while True:
#         game.print_board()
#         print()
#         row, col = current_player.get_move(game)
#         game.make_move(row, col, current_player.player_id)

#         if game.check_win(current_player.player_id):
#             game.print_board()
#             print(f"{current_player.name} (Player {current_player.player_id}) wins!")
#             break
#         elif game.is_draw():
#             game.print_board()
#             print("It's a draw!")
#             break

#         current_player = player2 if current_player == player1 else player1