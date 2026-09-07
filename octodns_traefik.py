import asyncio
import itertools
from logging import getLogger
from octodns.zone.base import DuplicateRecordException, SubzoneRecordException
from traefik import Router, TraefikClient
from typing import Dict, Optional, List

from octodns.record import Record
from octodns.source.base import BaseSource


class TraefikSource(BaseSource):
    SUPPORTS = ('A', 'AAAA', 'CNAME')
    SUPPORTS_GEO = False

    def __init__(self, id, traefik_api_url:str, default_record_set:Optional[list] = None, zones: Optional[dict] = None, default_ttl: int = 3600):
        klass = self.__class__.__name__
        self.log = getLogger(f'{klass}[{id}]')
        self.log.debug('__init__: id=%s', id)
        super().__init__(id)
        self.traefik_api_url = traefik_api_url
        self.default_record_set = default_record_set or []
        self.zones = zones or {}
        if len(self.zones) > 0:
            self.log.warning("Zone-based config is currently not supported. Ignoring...")
        self.client = TraefikClient(traefik_api_url)
        routers = asyncio.run(self._get_routers())
        self.hosts = self._get_hosts(routers)

    async def _get_routers(self) -> list[Router]:
        routers: list[Router]
        async with self.client as client:
            routers = await client.list_routers()
        return routers

    @staticmethod
    def _get_hosts(routers: list[Router]) -> set[str]:
        return set(list(itertools.chain(*[r.hostnames for r in routers])))

    @staticmethod
    def _is_subdomain(hostname: str, domain: str) -> bool:
        hostname = hostname.removesuffix(".").lower()
        domain = domain.removesuffix(".").lower()
        if not hostname or not domain:
            return False
        return hostname.endswith("." + domain)

    @staticmethod
    def _get_subdomain(hostname: str, domain: str) -> str:
        hostname = hostname.rstrip(".").lower()
        domain = domain.removesuffix(".").lower()
        return hostname.removesuffix("." + domain)

    def populate(self, zone, target=False, lenient=False):
        # This is the method adding records to the zone. For a source it's the
        # only thing that needs to be implemented. Again there's some best
        # practices wrapping our custom logic, mostly for logging/debug
        # purposes.
        self.log.debug(
            'populate: name=%s, target=%s, lenient=%s',
            zone.name,
            target,
            lenient,
        )

        before = len(zone.records)

        for hostname in self.hosts:
            if self._is_subdomain(hostname, zone.name):
                for rd in self.default_record_set:
                    record = Record.new(
                        zone, 
                        self._get_subdomain(hostname, zone.name),
                        rd,
                        source=self
                    )
                    try:
                        zone.add_record(record, lenient=lenient)
                    except SubzoneRecordException:
                        pass
                    except DuplicateRecordException:
                        self.log.info(
                            'populate:   duplicate record %s, skipping',
                            record,
                        )

        self.log.info(
            'populate:   found %s records, exists=False',
            len(zone.records) - before,
        )