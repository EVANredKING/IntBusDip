package com.teamcenter.app.repository;

import com.teamcenter.app.model.LSI;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface LSIRepository extends JpaRepository<LSI, Long> {
    Optional<LSI> findByName(String name);
} 