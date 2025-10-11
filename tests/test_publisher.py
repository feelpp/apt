"""Tests for AptlyPublisher class."""

from feelpp_aptly_publisher import AptlyPublisher


def test_normalize_component():
    """Test component name normalization."""
    # Test basic normalization
    pub = AptlyPublisher(component="Test_Component", distro="noble")
    assert pub.component == "test-component"

    # Test with spaces
    pub2 = AptlyPublisher(component="My Project Name", distro="noble")
    assert pub2.component == "my-project-name"

    # Test with special characters
    pub3 = AptlyPublisher(component="Feel++@2024", distro="noble")
    assert pub3.component == "feel-2024"

    # Test already normalized
    pub4 = AptlyPublisher(component="mmg", distro="noble")
    assert pub4.component == "mmg"


def test_publisher_init():
    """Test publisher initialization with defaults."""
    pub = AptlyPublisher(
        component="mmg",
        distro="noble",
    )
    assert pub.component == "mmg"
    assert pub.distro == "noble"
    assert pub.channel == "stable"
    assert pub.pages_repo == "https://github.com/feelpp/apt.git"
    assert pub.branch == "gh-pages"
    assert pub.sign is False
    assert pub.keyid is None


def test_publisher_init_custom():
    """Test publisher initialization with custom values."""
    pub = AptlyPublisher(
        component="my-project",
        distro="jammy",
        channel="testing",
        pages_repo="https://github.com/custom/apt.git",
        branch="main",
        sign=True,
        keyid="ABCD1234",
        verbose=True,
    )
    assert pub.component == "my-project"
    assert pub.distro == "jammy"
    assert pub.channel == "testing"
    assert pub.pages_repo == "https://github.com/custom/apt.git"
    assert pub.branch == "main"
    assert pub.sign is True
    assert pub.keyid == "ABCD1234"
    assert pub.verbose is True


def test_publisher_channels():
    """Test different channel values."""
    for channel in ["stable", "testing", "pr"]:
        pub = AptlyPublisher(component="test", distro="noble", channel=channel)
        assert pub.channel == channel


def test_publisher_distros():
    """Test different distribution values."""
    for distro in ["noble", "jammy", "focal", "bookworm", "bullseye"]:
        pub = AptlyPublisher(component="test", distro=distro)
        assert pub.distro == distro
