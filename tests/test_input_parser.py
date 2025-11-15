import sys
import input_parser
from unittest.mock import patch
from pytest import LogCaptureFixture


def test_parsing_required():
    testargs = ['prog', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-login', 'foo', '--from-org', 'my-org', '--to-org', 'my-org']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()

    assert args.from_disable_ssl_verify is False
    assert args.to_disable_ssl_verify is False
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
                '--to-url', 'https://to.git.com', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org']
    repos = ['spring-data-commons', 'spring-data-jpa', 'spring-amqp', 'spring-batch', 'spring-data-gemfire', 'spring-framework', 'spring-retry', 'spring-amqp-samples', 'spring-data-redis', 'spring-integration', 'spring-integration-samples', 'spring-data-cassandra', 'spring-net', 'spring-data-neo4j', 'spring-data-mongodb',
             'spring-webflow', 'spring-security', 'spring-security-kerberos', 'spring-shell', 'spring-plugin', 'spring-data-rest', 'spring-data-envers', 'spring-hateoas', 'spring-webflow-samples', 'eclipse-integration-tcserver', 'spring-integration-extensions', 'spring-boot', 'spring-loaded', 'spring-data-build', 'spring-petclinic']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
    assert input_parser.reduce(
        repos, args.repos_include, args.repos_exclude) == repos


def test_reduce_args_regexp_repos_set():
    testargs = ['prog', '--from-url', 'https://from.git.com',
                '--to-url', 'https://to.git.com', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org', '--repos-include', 'spring-p.*,spring-integration.*', '--repos-exclude', 'spring-plugin,spring-integration-.*']
    repos = ['spring-data-commons', 'spring-data-jpa', 'spring-amqp', 'spring-batch', 'spring-data-gemfire', 'spring-framework', 'spring-retry', 'spring-amqp-samples', 'spring-data-redis', 'spring-integration', 'spring-integration-samples', 'spring-data-cassandra', 'spring-net', 'spring-data-neo4j', 'spring-data-mongodb',
             'spring-webflow', 'spring-security', 'spring-security-kerberos', 'spring-shell', 'spring-plugin', 'spring-data-rest', 'spring-data-envers', 'spring-hateoas', 'spring-webflow-samples', 'eclipse-integration-tcserver', 'spring-integration-extensions', 'spring-boot', 'spring-loaded', 'spring-data-build', 'spring-petclinic']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
    assert input_parser.reduce(
        repos, args.repos_include, args.repos_exclude) == ['spring-integration', 'spring-petclinic']


def test_parsing_bool():
    testargs = ['prog', '--dry-run', '--from-url', 'https://from.git.com', '--from-disable-ssl-verify',
                '--to-url', 'https://to.git.com', '--to-disable-ssl-verify', '--to-login', 'foo', '--to-password', 'bar', '--from-org', 'my-org', '--to-org', 'my-org']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()

    assert args.from_disable_ssl_verify is True
    assert args.to_disable_ssl_verify is True
    assert args.dry_run is True


def test_display(caplog: LogCaptureFixture):
    testargs = ['prog', '--from-url', 'https://from.git.com', '--from-proxy', 'http://localhost:8000',
                '--to-url', 'https://to.git.com', '--to-proxy', 'http://evil:live@localhost:8000', '--to-login', 'ghu_xxxxxxxxxxxxxxxxxxxxxxxxx', '--from-org', 'my-org', '--to-org', 'my-org', '--to-description-prefix', 'Synchro - ']
    with patch.object(sys, 'argv', testargs):
        args = input_parser.parse()
    input_parser.print_args(args)

    assert 'Git "from" platform URL     : https://from.git.com' in caplog.text
    assert 'Git "from" login or token   : None' in caplog.text
    assert 'Git "from" proxy            : http://localhost:8000' in caplog.text
    assert 'Git "to" platform URL       : https://to.git.com' in caplog.text
    assert 'Git "to" login or token     : gh***************************' in caplog.text
    assert 'Git "to" proxy              : http://***@localhost:8000' in caplog.text
    assert 'Git "to" description prefix : Synchro - ' in caplog.text
