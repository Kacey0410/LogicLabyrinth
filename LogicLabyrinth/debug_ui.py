import tkinter as tk
from game import DungeonApp

app = DungeonApp()
print('app_created')
print('max_hp', app._max_hp)
print('buttons', app.btn_attack, app.btn_bag, app.btn_flee)
app.after(100, app.destroy)
app.mainloop()
