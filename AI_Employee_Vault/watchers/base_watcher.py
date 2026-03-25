"""
Base Watcher - Abstract base class for all AI Employee watchers.

All watchers follow the same pattern:
1. Continuously monitor a data source
2. Detect new/updated items
3. Create action files in the Needs_Action folder
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    Subclasses must implement:
    - check_for_updates(): Return list of new items to process
    - create_action_file(item): Create .md file in Needs_Action folder
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        
        # Track processed items to avoid duplicates
        self.processed_ids = set()
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check the data source for new or updated items.
        
        Returns:
            List of items that need processing
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create a markdown action file for an item.
        
        Args:
            item: The item to process
            
        Returns:
            Path to the created action file
        """
        pass
    
    def run(self):
        """
        Main run loop - continuously monitors and processes items.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f'Created action file: {filepath.name}')
                            except Exception as e:
                                self.logger.error(f'Error creating action file: {e}')
                    else:
                        self.logger.debug('No new items')
                except Exception as e:
                    self.logger.error(f'Error in check cycle: {e}')
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise
    
    def generate_filename(self, prefix: str, unique_id: str) -> str:
        """
        Generate a standardized filename.
        
        Args:
            prefix: File type prefix (e.g., 'EMAIL', 'FILE', 'WHATSAPP')
            unique_id: Unique identifier for the item
            
        Returns:
            Filename string with date
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f'{prefix}_{unique_id}_{date_str}.md'
    
    def create_frontmatter(self, item_type: str, **kwargs) -> str:
        """
        Create YAML frontmatter for action files.
        
        Args:
            item_type: Type of item (email, file, whatsapp, etc.)
            **kwargs: Additional frontmatter fields
            
        Returns:
            YAML frontmatter string
        """
        frontmatter = [
            '---',
            f'type: {item_type}',
            f'created: {datetime.now().isoformat()}',
            'status: pending',
        ]
        
        # Add custom fields
        for key, value in kwargs.items():
            frontmatter.append(f'{key}: {value}')
        
        frontmatter.append('---')
        return '\n'.join(frontmatter)
