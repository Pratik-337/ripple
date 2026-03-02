from app.services.impact.parser import parse_file

def test_parse_typescript_imports():
    content = open("tests/fixtures/ripple-mock-project/auth/validateUser.ts").read()
    result = parse_file("validateUser.ts", content)
    import_sources = [imp.source for imp in result.imports]
    assert "../shared/types" in import_sources
    
    export_names = [exp.name for exp in result.exports]
    assert "validateUser" in export_names

def test_parse_dashboard_dependency():
    content = open("tests/fixtures/ripple-mock-project/dashboard/UserPanel.tsx").read()
    result = parse_file("UserPanel.tsx", content)
    
    import_sources = [imp.source for imp in result.imports]
    assert "../auth/validateUser" in import_sources
