import sys
from unittest.mock import patch
import input_parser


def test_parsing_required():
    testargs = ['prog', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
        assert args.dry_run is False


def test_reduce_simple():
    assert input_parser.reduce([], '', '') == []
    assert input_parser.reduce(['a', 'b', 'c'], 'a,c', '\\.') == ['a', 'c']
    assert input_parser.reduce(['a', 'b', 'c'], '', 'b') == ['a', 'c']
    assert input_parser.reduce(['a', 'b', 'c'], 'a,c', 'b') == ['a', 'c']


def test_reduce_complex():
    repos = ['spring-data-commons', 'spring-data-jpa', 'spring-amqp', 'spring-batch', 'spring-data-gemfire', 'spring-framework', 'spring-retry', 'spring-amqp-samples', 'spring-data-redis', 'spring-integration', 'spring-integration-samples', 'spring-data-cassandra', 'spring-net', 'spring-data-neo4j', 'spring-data-mongodb',
             'spring-webflow', 'spring-security', 'spring-security-kerberos', 'spring-shell', 'spring-plugin', 'spring-data-rest', 'spring-data-envers', 'spring-hateoas', 'spring-webflow-samples', 'eclipse-integration-tcserver', 'spring-integration-extensions', 'spring-boot', 'spring-loaded', 'spring-data-build', 'spring-petclinic']
    assert input_parser.reduce(
        repos, 'eclipse-*', '\\.') == ['eclipse-integration-tcserver']
    assert input_parser.reduce(
        repos, 'spring-security*', 'spring-security-k*') == ['spring-security']
    assert input_parser.reduce(
        repos, 'spring-p.*,spring-integration.*', 'spring-plugin,spring-integration-.*') == ['spring-integration', 'spring-petclinic']


def test_reduce_args_regexp_repos_empty():
    testargs = ['prog', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org']
    repos = ['spring-data-commons', 'spring-data-jpa', 'spring-amqp', 'spring-batch', 'spring-data-gemfire', 'spring-framework', 'spring-retry', 'spring-amqp-samples', 'spring-data-redis', 'spring-integration', 'spring-integration-samples', 'spring-data-cassandra', 'spring-net', 'spring-data-neo4j', 'spring-data-mongodb',
             'spring-webflow', 'spring-security', 'spring-security-kerberos', 'spring-shell', 'spring-plugin', 'spring-data-rest', 'spring-data-envers', 'spring-hateoas', 'spring-webflow-samples', 'eclipse-integration-tcserver', 'spring-integration-extensions', 'spring-boot', 'spring-loaded', 'spring-data-build', 'spring-petclinic']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
        assert input_parser.reduce(
            repos, args.repos_include, args.repos_exclude) == repos


def test_reduce_args_regexp_repos_set():
    testargs = ['prog', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org', '--repos-include', 'spring-p.*,spring-integration.*', '--repos-exclude', 'spring-plugin,spring-integration-.*']
    repos = ['spring-data-commons', 'spring-data-jpa', 'spring-amqp', 'spring-batch', 'spring-data-gemfire', 'spring-framework', 'spring-retry', 'spring-amqp-samples', 'spring-data-redis', 'spring-integration', 'spring-integration-samples', 'spring-data-cassandra', 'spring-net', 'spring-data-neo4j', 'spring-data-mongodb',
             'spring-webflow', 'spring-security', 'spring-security-kerberos', 'spring-shell', 'spring-plugin', 'spring-data-rest', 'spring-data-envers', 'spring-hateoas', 'spring-webflow-samples', 'eclipse-integration-tcserver', 'spring-integration-extensions', 'spring-boot', 'spring-loaded', 'spring-data-build', 'spring-petclinic']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
        assert input_parser.reduce(
            repos, args.repos_include, args.repos_exclude) == ['spring-integration', 'spring-petclinic']


def test_parsing_dry_run():
    testargs = ['prog', '--dry-run', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-user', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
        assert args.dry_run is True
