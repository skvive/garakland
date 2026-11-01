package site.lexid.logshield;

import java.util.concurrent.atomic.AtomicLong;

/** Reject results from requests initiated on a screen that has since been replaced. */
public final class UiEpoch {
    private final AtomicLong epoch = new AtomicLong();
    public long current() { return epoch.get(); }
    public long invalidate() { return epoch.incrementAndGet(); }
    public boolean isCurrent(long issuedAt) { return issuedAt == epoch.get(); }
}
