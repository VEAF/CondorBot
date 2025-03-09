from condor.config import load_config, Config, CondorServerConfig

def test_load_config():
    
    config = load_config("tests/config_test.yaml")
    
    assert isinstance(config, Config)
    assert isinstance(config.condor_server, CondorServerConfig)
    assert config.condor_server.admin_password == "MyAdminPassword"
