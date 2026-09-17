import pytest
from services.code_scanner import find_usages


def test_find_usages_plain_identifier():
    """Finds direct function calls in TypeScript."""
    ts_code = b"""
import { createCompletion } from 'openai';

async function run() {
    const res = await createCompletion({ model: 'text-davinci-003' });
    console.log(res);
}
"""
    usages = find_usages("src/index.ts", ts_code, "createCompletion")
    assert len(usages) == 1
    u = usages[0]
    assert u["file_path"] == "src/index.ts"
    assert u["line_start"] == 5
    assert "createCompletion" in u["snippet"]


def test_find_usages_member_expression():
    """Finds method calls on objects in TypeScript / JavaScript."""
    ts_code = b"""
import { Configuration, OpenAIApi } from 'openai';

const openai = new OpenAIApi(new Configuration());

export async function generateText(prompt: string) {
    const response = await openai.createCompletion({
        model: "text-davinci-003",
        prompt: prompt,
    });
    return response.data;
}
"""
    usages = find_usages("src/ai.ts", ts_code, "createCompletion")
    assert len(usages) == 1
    u = usages[0]
    assert u["file_path"] == "src/ai.ts"
    assert u["line_start"] == 7
    assert "openai.createCompletion" in u["snippet"]


def test_find_usages_multiple_call_sites():
    """Discovers all occurrences across multiple lines."""
    ts_code = b"""
function test() {
    doAction(1);
    doOther();
    doAction(2);
}
"""
    usages = find_usages("src/test.ts", ts_code, "doAction")
    assert len(usages) == 2
    assert usages[0]["line_start"] == 3
    assert usages[1]["line_start"] == 5


def test_find_usages_no_match():
    """Returns empty list when symbol is not called."""
    ts_code = b"""
function example() {
    const x = 10;
    return x * 2;
}
"""
    usages = find_usages("src/math.ts", ts_code, "createCompletion")
    assert usages == []


def test_find_usages_tsx_syntax():
    """Parses React JSX/TSX syntax cleanly without syntax errors."""
    tsx_code = b"""
import React from 'react';
import { trackEvent } from 'analytics';

export function Button() {
    return (
        <button onClick={() => trackEvent('button_click')}>
            Click me
        </button>
    );
}
"""
    usages = find_usages("components/Button.tsx", tsx_code, "trackEvent")
    assert len(usages) == 1
    assert "trackEvent('button_click')" in usages[0]["snippet"]


def test_find_usages_python_syntax():
    """Finds direct and attribute calls in Python code."""
    py_code = b"""
def run():
    res = create_completion(model="gpt-4")
    other = client.create_completion(model="gpt-4o")
    return res
"""
    usages = find_usages("services/agent.py", py_code, "create_completion")
    assert len(usages) == 2
    assert usages[0]["file_path"] == "services/agent.py"
    assert usages[0]["line_start"] == 3
    assert 'create_completion(model="gpt-4")' in usages[0]["snippet"]
    assert usages[1]["line_start"] == 4
    assert 'client.create_completion(model="gpt-4o")' in usages[1]["snippet"]


def test_find_usages_python_fixture():
    """Finds usages inside the sample_service.py fixture file."""
    from pathlib import Path

    fixture_path = Path(__file__).parent / "fixtures" / "sample_service.py"
    with open(fixture_path, "rb") as f:
        py_code = f.read()

    usages = find_usages("tests/fixtures/sample_service.py", py_code, "create_completion")
    assert len(usages) == 2
    snippets = [u["snippet"] for u in usages]
    assert any('create_completion(model="gpt-4"' in s for s in snippets)
    assert any('client.create_completion(model="gpt-4o"' in s for s in snippets)
