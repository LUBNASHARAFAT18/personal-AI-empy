"""
Ralph Wiggum Loop - Autonomous multi-step task completion for Claude Code.

This implements the Stop hook pattern that keeps Claude working until tasks are complete
by re-injecting prompts when Claude tries to exit prematurely.

Usage:
    python ralph_wiggum.py AI_Employee_Vault --prompt "Process all emails" --max-iterations 10
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class RalphWiggumLoop:
    """
    Ralph Wiggum Stop hook for autonomous task completion.
    """

    def __init__(self, vault_path: str, max_iterations: int = 10,
                 completion_promise: str = 'TASK_COMPLETE'):
        """
        Initialize the Ralph loop.

        Args:
            vault_path: Path to Obsidian vault
            max_iterations: Maximum iterations before stopping
            completion_promise: String that indicates task completion
        """
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.current_iteration = 0
        self.logs_folder = self.vault_path / 'Logs'
        self.log_file = self.logs_folder / 'ralph_loop.json'
        
        # Ensure logs folder exists
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.start_time = None
        self.end_time = None
        self.iteration_logs = []

    def log_iteration(self, iteration: int, status: str, prompt: str, 
                     output: str = '', completion_detected: bool = False):
        """Log iteration details."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'iteration': iteration,
            'status': status,
            'prompt_length': len(prompt),
            'output_length': len(output),
            'completion_detected': completion_detected
        }
        
        self.iteration_logs.append(log_entry)
        
        # Save to file
        self._save_logs()

    def _save_logs(self):
        """Save logs to file."""
        logs_data = {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'max_iterations': self.max_iterations,
            'completion_promise': self.completion_promise,
            'iterations': self.iteration_logs
        }
        
        try:
            self.log_file.write_text(json.dumps(logs_data, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not save logs: {e}")

    def check_completion(self, output: str, done_folder: Optional[str] = None) -> bool:
        """
        Check if task is complete.

        Args:
            output: Claude's output text
            done_folder: Optional folder to check for completed files

        Returns:
            True if completion detected
        """
        # Check for completion promise in output
        if self.completion_promise in output:
            return True
        
        # Check if files moved to Done folder
        if done_folder:
            done_path = self.vault_path / done_folder
            if done_path.exists():
                # Check for recent files (last 5 minutes)
                cutoff = datetime.now().timestamp() - 300
                for f in done_path.iterdir():
                    if f.stat().st_mtime > cutoff:
                        return True
        
        return False

    def run(self, initial_prompt: str, done_folder: Optional[str] = None) -> Dict:
        """
        Run the Ralph Wiggum Loop.

        Args:
            initial_prompt: Initial task prompt
            done_folder: Optional folder to check for completion

        Returns:
            Loop execution summary
        """
        self.start_time = datetime.now()
        
        print(f"╔════════════════════════════════════════════════════════╗")
        print(f"║        RALPH WIGGUM LOOP - Autonomous Task Runner      ║")
        print(f"╚════════════════════════════════════════════════════════╝")
        print(f"\nConfiguration:")
        print(f"  Vault: {self.vault_path}")
        print(f"  Max Iterations: {self.max_iterations}")
        print(f"  Completion Promise: {self.completion_promise}")
        print(f"\nStarting loop...\n")
        
        prompt = initial_prompt
        
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1
            
            print(f"┌────────────────────────────────────────────────────┐")
            print(f"│ Iteration {self.current_iteration}/{self.max_iterations}")
            print(f"└────────────────────────────────────────────────────┘")
            print(f"\nPrompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n")
            
            # In real implementation, Claude Code would process here
            # For now, we simulate by waiting for user to run Claude
            print(f"⏳ Waiting for Claude Code to process...")
            print(f"   (In production, Claude would run automatically)")
            print(f"   (For testing, press Enter to simulate completion)")
            
            # Simulate Claude processing
            # In production, this would be replaced with actual Claude Code integration
            user_input = input("   Press Enter to continue or type 'complete' to finish: ")
            
            output = f"Simulated Claude output for iteration {self.current_iteration}"
            
            # Check for completion
            completion_detected = self.check_completion(output, done_folder)
            if user_input.lower() == 'complete' or 'TASK_COMPLETE' in user_input:
                completion_detected = True
            
            # Log iteration
            self.log_iteration(
                iteration=self.current_iteration,
                status='completed',
                prompt=prompt,
                output=output,
                completion_detected=completion_detected
            )
            
            if completion_detected:
                print(f"\n✅ Completion detected!")
                break
            else:
                print(f"\n⏭️  Task not complete, continuing...\n")
                # Re-inject prompt with context from previous iteration
                prompt = f"{initial_prompt}\n\n(Continuing from previous iteration. Task is not yet complete.)"
        
        self.end_time = datetime.now()
        self._save_logs()
        
        # Print summary
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"\n╔════════════════════════════════════════════════════════╗")
        print(f"║                    LOOP COMPLETE                        ║")
        print(f"╚════════════════════════════════════════════════════════╝")
        print(f"\nSummary:")
        print(f"  Iterations: {self.current_iteration}/{self.max_iterations}")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Completion: {'✅ Yes' if completion_detected else '❌ No'}")
        print(f"  Logs: {self.log_file}")
        
        return {
            'success': completion_detected,
            'iterations': self.current_iteration,
            'duration': duration,
            'completion_detected': completion_detected,
            'log_file': str(self.log_file)
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--prompt', type=str, help='Task prompt')
    parser.add_argument('--max-iterations', type=int, default=10, help='Max iterations')
    parser.add_argument('--completion-promise', type=str, default='TASK_COMPLETE',
                       help='Completion promise string')
    parser.add_argument('--done-folder', type=str, default='Done',
                       help='Folder to check for completion')
    
    args = parser.parse_args()
    
    # Get vault path
    if args.vault_path:
        vault_path = Path(args.vault_path).resolve()
    else:
        vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
        vault_path = vault_path.resolve()
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    loop = RalphWiggumLoop(
        str(vault_path),
        max_iterations=args.max_iterations,
        completion_promise=args.completion_promise
    )
    
    if args.prompt:
        result = loop.run(args.prompt, args.done_folder)
        sys.exit(0 if result['success'] else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
