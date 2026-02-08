from dataclasses import dataclass, asdict
import json, os
from pathlib import Path
import shutil
from typing import Dict, Any, Optional, List

@dataclass
class Node:
  """Represents a paragraph in a Fighting Fantasy book"""
  number: int
  battle: bool = False
  death: bool = False
  complete: bool = False
  # choice_text -> paragraph_number
  children: Dict[str, int] = None
  # how many child nodes visited
  children_visited: int = 0
  
  def __post_init__(self):
    if self.children is None:
      self.children = {}


class HouseOfHellTracker:
  """Tracks choices and builds decision tree for House of Hell"""
  
  FILENAME = "house-of-hell-tree.json"
  

  def __init__(self):
    self.tree: Dict[int, Node] = {}
    self.current_path: List[int] = []
    self.load_tree()
  

  def load_tree(self) -> None:
    """Load existing decision tree and current path from file"""
    if os.path.exists(self.FILENAME):
      try:
        with open(self.FILENAME, "r", encoding="utf-8") as f:
          data = json.load(f)
        # load tree
        if "tree" in data:
          for num_str, node_data in data["tree"].items():
            node = Node(**node_data)
            self.tree[int(num_str)] = node
        # load current path
        if "current_path" in data:
          self.current_path = data["current_path"]
          # truncate path to valid nodes only
          self.current_path = [n for n in self.current_path if n in self.tree]
      except (json.JSONDecodeError, KeyError, TypeError):
        print("Corrupted save file. Starting fresh.")
        self.tree = {}
        self.current_path = []


  def save_tree(self) -> None:
    """Save decision tree and current path to file atomically"""
    data = {
      "tree": {str(node.number): asdict(node) for node in self.tree.values()},
      "current_path": self.current_path
    }
    # write to temp file first
    temp_name = self.FILENAME + ".new"
    # with tempfile.NamedTemporaryFile(
    #   mode='w', suffix='.json', delete=False, encoding='utf-8'
    # ) as temp_f:
    #   json.dump(data, temp_f, indent=2, ensure_ascii=False)
    #   temp_path = temp_f.name
    # with open(self.FILENAME, "w", encoding="utf-8") as f:
    #   json.dump(data, f, indent=2, ensure_ascii=False)
    with open(temp_name, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    # atomic rename/replace or create-if-missing
    shutil.move(temp_name, self.FILENAME)
    # os.replace(temp_name, self.FILENAME)
    # try:
      # atomically replace the original
      # os.replace(temp_name, self.FILENAME)
      # shutil.move(temp_path, self.FILENAME)
    # except Exception:
      # cleanup temp file on failure
      # os.unlink(temp_path)
      # print("⚠️  Failed to save tree.")
  

  def add_or_update_node(
    self,
    number:int,
    battle:bool=False,
    death:bool=False,
    complete:bool=True,
    choices:Optional[Dict[str, int]]=None,
  ) -> None:
    """Add or update a node in the tree"""
    node = self.tree.get(number, Node(number))
    node.battle = battle
    node.death = death
    node.complete = complete

    if choices:
      node.children.update(choices)
      # ensure all target paragraphs exist as incomplete nodes
      for _, next_num in choices.items():
        if next_num not in self.tree:
          self.tree[next_num] = Node(number=next_num, complete=False)

    self.tree[number] = node
  

  def go_to_paragraph(self, number: int) -> None:
    """Navigate to a paragraph and track the path"""
    node = self.tree.get(number)

    # auto-edit if empty
    if (
      node and
      # not node.complete and
      not node.battle and
      not node.death and
      not node.children
     ):
      print(f"Empty stub node {number}. Please describe what happens here.")
      self.prompt_for_node(number)
    elif number not in self.tree:
      print(f"New paragraph {number}. Please describe what happens here.")
      self.prompt_for_node(number)

    # increment children_visited count for PARENT node
    if len(self.current_path) > 1:
      parent_sum = self.current_path[-2]
      parent_node = self.tree[parent_num]
      if number in parent_node.children.values():
        parent_node.children_visited += 1

    # truncate path when going back
    try:
      idx = self.current_path.index(number)
      if idx < len(self.current_path) - 1:
        print(f"Going back to ¶{number}")
      self.current_path = self.current_path[:idx + 1]
    except ValueError:
      # go forward, append
      self.current_path.append(number)

    # # remove any existing occurrences of this number from path
    # while number in self.current_path:
    #   self.current_path.remove(number)

    # append paragraph number
    # self.current_path.append(number)
    self.display_status(number)


  def display_status(self, number: int) -> None:
    """Display current paragraph status with colour coding"""
    node = self.tree[number]
    
    if node.death:
      print(f"\033[91m¶{number:3d} 💀 DEATH\033[0m")
    elif not node.complete:
      print(f"\033[93m¶{number:3d} ⚠️  INCOMPLETE\033[0m")
    elif node.battle:
      print(f"\033[91m¶{number:3d} ⚔️  BATTLE\033[0m")
    else:
      print(f"\033[92m¶{number:3d} ✅ COMPLETE\033[0m")
    
    print(f"  Children: {len(node.children)}")
    if node.children:
      for choice, next_num in sorted(node.children.items()):
        # ensure a Node exists for each child; if missing, create incomplete one
        marker_node = self.tree.get(next_num)
        if marker_node is None:
          marker_node = Node(number=next_num, complete=False)
          self.tree[next_num] = marker_node

        # marker = "" if self.tree.get(next_num, Node(next_num)).complete else "⚠️"
        marker = "" if marker_node.complete else "⚠️"
        print(f"    → {choice:<20} ¶{next_num:3d} {marker}")
    else:
      print("  (No children defined yet.)")
  

  def prompt_for_node(self, number:int) -> None:
    """Interactive prompt to fill and edit node information"""
    # always create/update node first
    # marked as incomplete until editing finishes
    self.add_or_update_node(number, complete=False)

    existing = self.tree.get(number)
    print(f"\n--- Paragraph {number} ---")

    if existing:
      # show current status
      print("\nCurrent status:")
      kind = "normal"
      if existing.death:
        kind = "death"
      elif existing.battle:
        kind = "battle"
      print(f"  Type: {kind}")
      print(f"  Complete: {existing.complete}")
      if existing.children:
        print("  Choices:")
        for i, (choice_text, next_num) in enumerate(existing.children.items(),
                                                    start=1):
          print(f"   {i}. {choice_text!r} -> {next_num}")
      else:
        print("  Choices: (none)")
    else:
      print("New paragraph.")
    
    # edit menu loop
    while True:
      print("\nWhat do you want to do?")
      print("1. Set or change type (battle/death/normal)")
      print("2. Add or edit choices")
      print("3. Delete a single choice")
      print("4. Delete ALL choices")
      print("5. Delete this node completely")
      # print("6. Finish editing")
      action = input("Enter choice (1-5, ENTER to finish): ").strip()
      
      # ENTER -> finish editing
      if action == "":
        break

      if action == "1":
        # set type and mark complete
        while True:
          print("\nWhat happens here?")
          print("1. Battle")
          print("2. Death") 
          print("3. Normal paragraph")
          t = input("Enter choice (1-3): ").strip()
      
          if t == "1":
            self.add_or_update_node(number, battle=True, death=False, complete=False)
            break
          elif t == "2":
            self.add_or_update_node(number, battle=False, death=True, complete=False)
            break
          elif t == "3":
            self.add_or_update_node(number, battle=False, death=False, complete=False)
            break
        existing = self.tree[number]
      elif action == "2":
        # add or overwrite choices for this node
        print("\nAdd choices (ENTER on empty choice to stop).")
        while True:
          choice_text = input("Choice text (or ENTER to finish): ").strip()
          if not choice_text:
            break
          try:
            next_num = int(input("  Goes to paragraph: "))
            # merge choices into existing children
            self.add_or_update_node(
              number, choices={choice_text: next_num}, complete=False
            )
          except ValueError:
            print("  Invalid paragraph number.")
        # existing = self.tree.get(number)
      elif action == "3":
        # delete single choice
        existing = self.tree.get(number)
        if not existing or not existing.children:
          print("No choices to delete.")
          continue
        print("\nChoices:")
        choices_list = list(existing.children.items())
        for i, (choice_text, next_num) in enumerate(choices_list, start=1):
          print(f"  {i}. {choice_text!r} -> {next_num}")
        try:
          idx = int(input("Delete which choice number? ")) - 1
          if 0 <= idx < len(choices_list):
            key_to_delete = choices_list[idx][0]
            del existing.children[key_to_delete]
            print("Choice deleted.")
          # else:
          #   print("Invalid choice number.")
        except ValueError:
          print("Invalid number.")
      elif action == "4":
        # delete all choices
        existing = self.tree.get(number)
        if existing:
          existing.children.clear()
          print("All choices deleted.")
      elif action == "5":
        # delete this node entirely
        confirm = input("Really delete this node? (y/N): ").strip().lower()
        if confirm == "y":
          if number in self.tree:
            del self.tree[number]
          # also remove references to this node from other nodes' children
          for node in self.tree.values():
            to_delete = [c for c, dest in node.children.items() if dest == number]
            for c in to_delete:
              del node.children[c]
          print("Node deleted.")
          # leave editing
          return
          # break
      # elif action == "6":
      #   break
      else:
        print("Please enter a number between 1 and 5 or press ENTER.")
    
    # # add choices
    # while True:
    #   choice_text = input("\nChoice text (or ENTER to finish): ").strip()
    #   if not choice_text:
    #     break
    #   try:
    #     next_num = int(input("Goes to paragraph: "))
    #     self.add_or_update_node(number, choices={choice_text: next_num})
    #   except ValueError:
    #     print("Invalid paragraph number.")
    
    node = self.tree[number]
    # make node complete if info was added
    if node.battle or node.death or node.children:
      self.add_or_update_node(number, complete=True)
    else:
      print(f"Paragraph {number} left as stub (incomplete).")

    self.save_tree()
  

  def show_tree_overview(self) -> None:
    """Show overview of explored tree"""
    title = "\n📖 ═══  HOUSE OF 💀HELL💀 TREE OVERVIEW  ═══ 📖\n"
    print(title)
    # print("🗡️".ljust(len_title - 19, '═'))
    # print("=" * 50)
    
    deaths = sum(1 for node in self.tree.values() if node.death)
    battles = sum(1 for node in self.tree.values() if node.battle)
    incomplete = sum(1 for node in self.tree.values() if not node.complete)
    
    print(f"Total paragraphs: {len(self.tree)}")
    print(f"💀  Deaths: {deaths}")
    print(f"⚔️  Battles: {battles}")
    print(f"⚠️  Incomplete: {incomplete}")
    
    # print("\nCurrent path:", " → ".join(map(str, self.current_path[-5:])))
    # print("\nCurrent path:", " → ".join(map(str, self.current_path)))
    if self.current_path:
      current = self.current_path[-1]
      highlighted_path = ' → '.join(
        f"\033[30;103m{n}\033[0m" if n == current else str(n)
        for n in self.current_path
      )
      print("\nCurrent path:", highlighted_path)
    else:
      print("\nCurrent path: (at start)")
  

  def backtrack(self) -> None:
    """Go back one paragraph in path"""
    if self.current_path:
      self.current_path.pop()
      if self.current_path:
        print(f"Back to ¶{self.current_path[-1]}")
        self.display_status(self.current_path[-1])
      else:
        print("Back to start.")
    else:
      print("Already at start.")


  def print_tree(self, root:int=1) -> None:
    """Print a 2D ASCII tree of all explored paths from `root`"""
    if root not in self.tree:
      print(f"Root paragraph {root} is not in the tree yet.")
      return

    title = "\n💀 🗡️  HOUSE OF HELL TREE  🗡️ 💀\n"
    print(title)

    # fast lookup for current path highlighting
    current_set = set(self.current_path)

    def status_emoji(node:Node) -> str:
      if node.death:
        return "💀"
      if node.battle:
        return "⚔️"
      if node.children:
        # read but has unexplored children
        return "📖"
      if node.children_visited == len(node.children) and node.children:
        # all children nodes explored
        return "✅"
      if node.complete:
        # leaf node, complete
        return "✅"
      # incomplete stub
      return "⚠️"

    def status_label(node:Node) -> str:
      if node.death:
        return "D"
      if node.battle:
        return "B"
      if node.children:
        return "P" # partial (unexplored children nodes)
      if node.children_visited == len(node.children) and node.children:
        return "F" # all children nodes explored
      if node.complete:
        return "C" # complete leaf
      return "I" # incomplete

    def marker(node_num:int) -> str:
      # highlight current path node
      # return " ⬅ current" if node_num in current_set else ""
      return " ⬅ current" if node_num == self.current_path[-1] else ""
    
    def dfs(node_num:int, prefix:str="", is_last:bool=True) -> None:
      node = self.tree.get(node_num)
      if node is None:
        # create implicit incomplete node if it is referenced but not stored
        node = Node(number=node_num, complete=False)
        self.tree[node_num] = node

      connector = "└──" if is_last else "├──"
      emoji = status_emoji(node)
      label = status_label(node)
      print(f"{prefix}{connector} [{node_num}] {emoji} ({label}){marker(node_num)}")

      children_items = sorted(node.children.items(), key=lambda kv: kv[1])
      if not children_items:
        return

      # next prefix for children
      child_prefix = prefix + ("    " if is_last else "│   ")

      for idx, (_, child_num) in enumerate(children_items):
        last_child = (idx == len(children_items) - 1)
        dfs(child_num, child_prefix, last_child)

    # root printed without prefix
    root_node = self.tree.get(root)
    if root_node is None:
      root_node = Node(number=root, complete=False)
      self.tree[root] = root_node

    print(
      f"[{root}] {status_emoji(root_node)} ({status_label(root_node)}) {marker(root)}"
    )
    children_items = sorted(root_node.children.items(), key=lambda kv: kv[1])

    for idx, (_, child_num) in enumerate(children_items):
      last_child = (idx == len(children_items) - 1)
      dfs(child_num, "", last_child)

    print()


def main() -> None:
  """Main game loop"""
  tracker = HouseOfHellTracker()
  
  title = "🏰 HOUSE OF HELL 🏰 - Decision Tree Tracker"
  # len_title = len(title)
  print(title)
  print("🗡️"*21)
  print(
    "\nCommands: go <number>, overview, tree [root], back, edit <number>, quit"
  )
  
  while True:
    cmd = input("\n> ").strip().lower().split()
    if not cmd:
      continue
    
    if cmd[0].lower() == "quit":
      tracker.save_tree()
      print("Tree saved. Goodbye! ☾")
      break
    elif cmd[0].lower() == "go" and len(cmd) == 2:
      try:
        num = int(cmd[1])
        tracker.go_to_paragraph(num)
      except ValueError:
        print("Please enter: go <paragraph_number>")
    elif cmd[0].lower() == "overview":
      tracker.show_tree_overview()
    elif cmd[0].lower() == "tree":
      if len(cmd) == 2:
        try:
          root = int(cmd[1])
          tracker.print_tree(root=root)
        except ValueError:
          print("Please enter: tree <paragraph number>")
      else:
        # default root = 1
        tracker.print_tree()
    elif cmd[0].lower() == "back":
      tracker.backtrack()
    elif cmd[0].lower() == "edit" and len(cmd) == 2:
      try:
        num = int(cmd[1])
        tracker.prompt_for_node(num)
      except ValueError:
        print("Please enter: edit <paragraph number>")
    else:
      print(
        "Commands: go <number>, overview, tree [root], back, edit <number>, quit"
      )

if __name__ == "__main__":
  main()
