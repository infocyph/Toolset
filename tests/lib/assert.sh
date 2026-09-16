#!/usr/bin/env bash

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  return 1
}

pass() {
  printf 'PASS: %s\n' "$*"
}

assert_eq() {
  local expected="${1-}" actual="${2-}" message="${3:-values differ}"
  [[ "$actual" == "$expected" ]] || fail "$message (expected=$(printf '%q' "$expected"), actual=$(printf '%q' "$actual"))"
}

assert_status() {
  local expected="$1" actual="$2" message="${3:-unexpected exit status}"
  [[ "$actual" -eq "$expected" ]] || fail "$message (expected=$expected, actual=$actual)"
}

assert_contains() {
  local haystack="${1-}" needle="${2-}" message="${3:-expected text not found}"
  [[ "$haystack" == *"$needle"* ]] || fail "$message (missing=$(printf '%q' "$needle"))"
}
