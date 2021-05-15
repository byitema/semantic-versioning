import re


class Version:
    _REGEXP = re.compile(r'^(?P<major>0|[1-9]\d*)'
    '\.(?P<minor>0|[1-9]\d*)'
    '\.(?P<patch>0|[1-9]\d*)'
    '(?P<pre_release>(?P<shorten_pre_release>a|b|rc|r|alpha|beta|release|release_candidate)?'
    '|(?P<default_pre_release>-((0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?)$')

    _PRIORITY = {
        'alpha': 0,
        'beta': 1,
        'release_candidate': 2,
        'release': 3,
    }

    _SHORTENING = {
        'a': 'alpha',
        'b': 'beta',
        'rc': 'release_candidate',
        'r': 'release'
    }

    @classmethod
    def parse(cls, version):
        match = cls._REGEXP.match(version)
        if match is None:
            raise ValueError(f'{version} is not valid version')

        return (
            match['major'],
            match['minor'],
            match['patch'],
            match['shorten_pre_release'],
            match['default_pre_release']
        )

    @classmethod
    def replace_shortening(cls, shorten_string: str):
        if shorten_string in ('a', 'b', 'rc', 'c'):
            return cls._SHORTENING[shorten_string]

        if shorten_string not in ('alpha', 'beta', 'release_candidate', 'release'):
            return int(shorten_string)

        return shorten_string

    @classmethod
    def partial_compare(cls, o1, o2):
        """
        Compare parts of version.

        For example, it helps to decide how to compare 'alpha' and 1, 'alpha' and 'beta', etc.
        """

        if isinstance(o1, int):
            if isinstance(o2, int):
                return 1 if o1 > o2 else 0 if o1 == o2 else -1
            elif isinstance(o2, str):
                return -1
        elif isinstance(o1, str):
            if isinstance(o2, int):
                return 1
            elif isinstance(o2, str):
                return 1 if cls._PRIORITY[o1] > cls._PRIORITY[o2]\
                    else 0 if cls._PRIORITY[o1] == cls._PRIORITY[o2] else -1

    def compare(self, other):
        """
        Compare full versions.

        First of all major, minor and patch versions are compared.
        Then the next situation is handled: Versions have equal major, minor and patch versions,
        and one of them has no pre-release.
        If both Versions have pre-release versions, they are being compared, and if they are equal as well,
        the number of parts in the pre-release is compared.
        """

        if not isinstance(other, self.__class__):
            return NotImplemented

        if self.main_version > other.main_version:
            return 1
        elif self.main_version < other.main_version:
            return -1

        if self.pre_release_len == 0 and other.pre_release_len == 0:
            return 0
        elif self.pre_release_len == 0:
            return 1
        elif other.pre_release_len == 0:
            return -1

        min_len = min(self.pre_release_len, other.pre_release_len)
        for i in range(min_len):
            if self.partial_compare(self.pre_release[i], other.pre_release[i]) == 1:
                return 1
            elif self.partial_compare(self.pre_release[i], other.pre_release[i]) == -1:
                return -1

        if self.pre_release_len > other.pre_release_len:
            return 1
        elif self.pre_release_len < other.pre_release_len:
            return -1

        return 0

    def __init__(self, version):
        major, minor, patch, shorten_pre_release, default_pre_release = self.parse(version)

        self.main_version = tuple([int(major), int(minor), int(patch)])

        # replacing all shortening in pre-release with complete names for easier comparison ('a' - 'alpha', etc.)
        if shorten_pre_release is None:
            if default_pre_release is not None:
                self.pre_release = tuple(self.replace_shortening(x) for x in default_pre_release[1:].split('.'))
            else:
                self.pre_release = tuple()
        else:
            self.pre_release = tuple([self.replace_shortening(shorten_pre_release)])

        self.pre_release_len = len(self.pre_release)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (
            self.main_version == other.main_version
            and self.pre_release == other.pre_release
        )

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.compare(other) == -1


def main():
    to_test = [
        ("1.0.0", "2.0.0"),
        ("1.0.0", "1.42.0"),
        ("1.2.0", "1.2.42"),
        ("1.1.0-alpha", "1.2.0-alpha.1"),
        ("1.0.1b", "1.0.10-alpha.beta"),
        ("1.0.0-rc.1", "1.0.0"),
    ]

    for version_1, version_2 in to_test:
        assert Version(version_1) < Version(version_2), "le failed"
        assert Version(version_2) > Version(version_1), "ge failed"
        assert Version(version_2) != Version(version_1), "neq failed"


if __name__ == "__main__":
    main()
