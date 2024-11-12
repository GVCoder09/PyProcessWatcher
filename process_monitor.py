from datetime import datetime
import wmi
import win32api
import win32con
import win32security


class ProcessMonitor():
    """Сlass defines a processes monitor object."""

    def __init__(self, notify_filter='operation'):
        """Initialize an instance of the class.

        Args:
          action (str): Type monitored operation. It can take the following
            values:
            - 'operation': All possible operations with processes.
            - 'creation': Creating a process.
            - 'deletion': Deleting a process.
            - 'modification': Process modification.

        Raises:
          ProcMonitorError: When errors occur when watcher installation error.
        """
        valid_notify_filter = (
            'operation',
            'creation',
            'deletion',
            'modification'
        )
        if notify_filter not in valid_notify_filter:
            raise ProcessMonitorError(
                'Watcher installation error.'
                f'The notify_filter value cannot be: "{notify_filter}".'
            )
        self._process_property = {
            'EventType': None,
            'Caption': None,
            'Owner': None,
            'Privileges': None,
            'CommandLine': None,
            'CreationDate': None,
            'Description': None,
            'ExecutablePath': None,
            'HandleCount': None,
            'Name': None,
            'ParentProcessId': None,
            'ProcessID': None,
            'ThreadCount': None,
            'TimeStamp': None,
        }

        HKLM = 0x80000002
        registry = wmi.Registry()
        registry.EnumKey(
            hDefKey=HKLM, sSubKeyName=r"Software\Microsoft\Windows\CurrentVersion\Uninstall")

        self._process_watcher = wmi.WMI().Win32_Process.watch_for(
            notify_filter
        )

    def update(self):
        """Update the properties of a process when the event occurs.

        This function updates the dict with process properties when a particular
        event occurs with the process. Process properties can be obtained from
        the corresponding class attribute.
        """
        process = self._process_watcher()
        self._process_property['EventType'] = process.event_type
        self._process_property['Caption'] = process.Caption
        try:
            if process.GetOwner()[1] == 2:
                self._process_property['Owner'] = 'Access denied'
            else:
                self._process_property['Owner'] = f'{
                    process.GetOwner()[0]}\\{process.GetOwner()[2]}'
        except:
            self._process_property['Owner'] = 'Access denied'
        self._process_property['Privileges'] = self.get_process_privileges(
            process.ProcessID)
        self._process_property['CommandLine'] = process.CommandLine
        self._process_property['CreationDate'] = datetime.strptime(
            process.CreationDate[:-4], '%Y%m%d%H%M%S.%f').strftime("%d-%m-%Y %H:%M:%S")
        self._process_property['Description'] = process.Description
        self._process_property['ExecutablePath'] = process.ExecutablePath
        self._process_property['HandleCount'] = process.HandleCount
        self._process_property['Name'] = process.Name
        self._process_property['ParentProcessId'] = process.ParentProcessId
        self._process_property['ProcessID'] = process.ProcessID
        self._process_property['ThreadCount'] = process.ThreadCount
        self._process_property['TimeStamp'] = datetime.today().strftime(
            '%d-%m-%Y %H:%M:%S')

    def get_process_privileges(self, pid):

        try:
            hproc = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION, False, pid
            )
            htok = win32security.OpenProcessToken(hproc, win32con.TOKEN_QUERY)
            privs = win32security.GetTokenInformation(
                htok, win32security.TokenPrivileges
            )
            privileges = ''
            for priv_id, flags in privs:
                if flags == (win32security.SE_PRIVILEGE_ENABLED |
                             win32security.SE_PRIVILEGE_ENABLED_BY_DEFAULT):
                    privileges += f'{win32security.LookupPrivilegeName(None,
                                                                       priv_id)}|'
        except Exception:
            privileges = 'N/A'

        return privileges

    @property
    def timestamp(self):
        """Timestamp of the event occurrence."""
        return self._process_property['TimeStamp']

    @property
    def event_type(self):
        """Type of event that occurred."""
        return self._process_property['EventType']

    @property
    def caption(self):
        """Short description of an object—a one-line string."""
        return self._process_property['Caption']

    @property
    def owner(self):
        ''' Owner '''
        return self._process_property['Owner']

    @property
    def privileges(self):
        ''' Privileges '''
        return self._process_property['Privileges']

    @property
    def command_line(self):
        """Command line used to start a specific process, if applicable."""
        return self._process_property['CommandLine']

    @property
    def creation_date(self):
        """Date and time the process begins executing."""
        return self._process_property['CreationDate']

    @property
    def description(self):
        """Description of an object."""
        return self._process_property['Description']

    @property
    def executable_path(self):
        """Path to the executable file of the process."""
        return self._process_property['ExecutablePath']

    @property
    def handle_count(self):
        """Total number of open handles owned by the process."""
        return self._process_property['HandleCount']

    @property
    def name(self):
        """Name of the executable file responsible for the process."""
        return self._process_property['Name']

    @property
    def parent_process_id(self):
        """Unique identifier of the process that creates a process."""
        return self._process_property['ParentProcessId']

    @property
    def process_id(self):
        """Numeric identifier used to distinguish one process from another."""
        return self._process_property['ProcessID']

    @property
    def thread_count(self):
        """Number of active threads in a process."""
        return self._process_property['ThreadCount']


class ProcessMonitorError(Exception):
    """ Class of exceptions """
