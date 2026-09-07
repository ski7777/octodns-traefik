import asyncio
import itertools
from logging import getLogger
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
        self.routers = asyncio.run(self.client.list_routers())
        routers = asyncio.run(self._get_routers)
        self.hosts = self._get_hosts(routers)
        self.log.info(self.hosts)

    async def _get_routers(self) -> list[Router]:
        routers: list[Router]
        async with self.client:
            routers = await self.client.list_routers()
        return routers

    def _get_hosts(self, routers: list[Router]) -> set[str]:
        return set(list(itertools.chain(*[r.hostnames for r in routers])))

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

        self.log.info(
            'populate:   found %s records, exists=False',
            len(zone.records) - before,
        )